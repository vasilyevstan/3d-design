"""Minimal one-wall display stand for Margaret.  She stands on her keel like a yacht ashore: the printed flat under the
ballast bulb sits in a shallow locating pocket in the base, and ONE upright wall just forward of the bulb nose holds her
upright.  The wall notch is the vertical-sweep hull-section envelope over the wall thickness, grown by a 0.3 mm disc, with
a 0.4 mm chamfer on both rims; the pocket is the bulb section at base-top height grown by 0.4 mm, rim chamfered.  The bulb
flat spans the centre of gravity for every load case, so the keel carries the weight (compression on the bulb joint) and
the wall only stops roll and nose-down pitch.  One navy piece, printed upright as-is, no supports.
Run: MARGARET_OUT=<v7 build dir> STAND_OUT=<dir> blender -b --factory-startup -P stand_v7.py
Writes Stand.stl (assembled boat coordinates, mm), Stand-bed.stl (placed on a 256 mm bed) and stand.json."""
import os, json, math, struct, bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

OUT, SOUT = os.environ["MARGARET_OUT"], os.environ["STAND_OUT"]
os.makedirs(SOUT, exist_ok=True)
HULL = ["Lower_blue", "Lower_white", "Lower_ink", "Upper_white", "Upper_ink", "Upper_teak"]
APPENDAGES = ["Fin_cap", "Ballast_cup", "Rudder", "Rudder_ink"]
PLATE_T, CLEAR, ARM, Z_TOP = 4.0, 0.3, 3.2, -3.0
CHAMFER, NRS = 0.4, 2000
WALL_GAP = 5.0                  # wall rear face to the bulb nose
BASE_T, BASE_W_MIN, BASE_R, BASE_CH, BASE_MARGIN = 4.0, 50.0, 10.0, 0.8, 6.0
POCKET_D, POCKET_CLEAR, POCKET_VGAP = 0.8, 0.4, 0.6   # VGAP: bulb tail/nose height over the base top
FOOT_HW = 13.0
FLOOR_DROP, FLOOR_HW = 1.0, 8.0  # notch floor relief: hull never lands on the wall, the keel flat carries the weight
TAIL_MARGIN = 2.0               # base runs aft past the bulb tail so a nose-up rock lands the tail on the plank
PLA_STAND_G_PER_CM3 = 0.865     # sliced grams / solid cm3 of the v7f stand (15 % infill, 3 walls)


def load(names):
    verts, polys = [], []
    for n in names:
        p = os.path.join(OUT, n+".stl")
        if not os.path.exists(p):
            continue
        bpy.ops.wm.stl_import(filepath=p)
        ob = bpy.context.selected_objects[0]
        base = len(verts)
        verts += [ob.matrix_world @ v.co for v in ob.data.vertices]
        polys += [tuple(base+i for i in pl.vertices) for pl in ob.data.polygons]
        bpy.data.objects.remove(ob, do_unlink=True)
    return verts, polys


hv, hp = load(HULL)
hull = BVHTree.FromPolygons(hv, hp)
av, ap = load(APPENDAGES)
app = BVHTree.FromPolygons(av, ap)
cv, cpl = load(["Ballast_cup"])
cup = BVHTree.FromPolygons(cv, cpl)
z_flat = min(v.z for v in av)                       # printed flat under the bulb = keel contact
flat = [v for v in av if v.z < z_flat+0.02]
FLAT_X = (min(v.x for v in flat), max(v.x for v in flat))
FLAT_HY = max(abs(v.y) for v in flat)
Z_BASE = z_flat+POCKET_D                             # base top; the pocket floor is the flat
bulb_av = [v for v in av if v.x > -60.0]             # fin cap + cup (rudder excluded)
APP_NOSE_X = max(v.x for v in bulb_av)
BULB_TAIL_X = min(v.x for v in cv)
TAIL = min(cv, key=lambda v: v.x)                    # bulb tail tip: the nose-up pivot once it lands on the plank
WALL_X = APP_NOSE_X+WALL_GAP+PLATE_T/2


def half_breadth(x, z):
    out = []
    for sgn in (1, -1):
        hit = hull.ray_cast(Vector((x, sgn*90.0, z)), Vector((0, -sgn, 0)))
        if hit[0] is not None:
            out.append(sgn*hit[0].y)
    return max(out) if out else None


def keel_z(x):
    hit = hull.ray_cast(Vector((x, 0.0, -150.0)), Vector((0, 0, 1)))
    return hit[0].z


def notch_profile(x0, clear=CLEAR):
    xs = [x0+PLATE_T*(k/8-0.5) for k in range(9)]
    zk = min(keel_z(x) for x in xs)
    dz = 0.05
    zs = [zk+dz*i for i in range(int((Z_TOP+CLEAR+CHAMFER+1.5-zk)/dz)+1)]
    b = []
    for z in zs:
        hb = [h for h in (half_breadth(x, z) for x in xs) if h is not None]
        b.append(max(hb) if hb else 0.0)
    nk = int(round(clear/dz))
    prof = []
    for i in range(-nk, len(zs)):
        z = zk+dz*i
        best = -1.0
        for j in range(max(0, i-nk), min(len(zs), i+nk+1)):
            d = (j-i)*dz
            best = max(best, b[j]+math.sqrt(max(0.0, clear*clear-d*d)))
        if best > 0:
            prof.append((best, z))
    return zk, prof


def deepen(prof, hw):
    """Notch profile with the floor dropped FLOOR_DROP over |y| <= hw (flanks above keep their clearance)."""
    zb = prof[0][1]-FLOOR_DROP
    k = 3.0                                          # compact smooth max: rounds the relief/flank corner only

    def smax(a, b):
        h = max(k-abs(a-b), 0.0)/k
        return max(a, b)+h*h*k/4
    return [(hw, zb)]+[(smax(y, hw), z) for y, z in prof]


def notch_poly(prof, z_cap):
    """Closed notch outline (y, z): right flank up, out over the arm top, left flank down."""
    prof = [q for q in prof if q[1] <= z_cap]
    poly = list(prof) + [(prof[-1][0]+4.0, prof[-1][1]+2.0), (-prof[-1][0]-4.0, prof[-1][1]+2.0)]
    return poly + [(-y, z) for y, z in reversed(prof)]


def resample(poly, n):
    """n points evenly spaced by arc length round the closed polygon, starting at poly[0]."""
    seg = [math.dist(a, b) for a, b in zip(poly, poly[1:]+poly[:1])]
    tot, out, k, acc = sum(seg), [], 0, 0.0
    for i in range(n):
        t = tot*i/n
        while acc+seg[k] < t:
            acc += seg[k]; k += 1
        a, b = poly[k], poly[(k+1) % len(poly)]
        f = (t-acc)/seg[k] if seg[k] else 0.0
        out.append((a[0]+f*(b[0]-a[0]), a[1]+f*(b[1]-a[1])))
    return out


def link(name, bm):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob


def rings_solid(name, rings):
    bm = bmesh.new()
    R = [[bm.verts.new(p) for p in r] for r in rings]
    for r0, r1 in zip(R, R[1:]):
        L = len(r0)
        for j in range(L):
            bm.faces.new((r0[j], r0[(j+1) % L], r1[(j+1) % L], r1[j]))
    bm.faces.new(list(reversed(R[0]))); bm.faces.new(R[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return link(name, bm)


def prism_x(name, poly_yz, x0, x1):
    return rings_solid(name, [[(x, y, z) for y, z in poly_yz] for x in (x0, x1)])


def rrect(x0, x1, y0, y1, r, seg=10):
    pts = []
    for cx, cy, a0 in ((x1-r, y0+r, -90), (x1-r, y1-r, 0), (x0+r, y1-r, 90), (x0+r, y0+r, 180)):
        for k in range(seg+1):
            a = math.radians(a0+90*k/seg)
            pts.append((cx+r*math.cos(a), cy+r*math.sin(a)))
    return pts


def boolean(a, b, op):
    m = a.modifiers.new("b", "BOOLEAN"); m.operation = op; m.object = b; m.solver = "EXACT"
    me = bpy.data.meshes.new_from_object(a.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    a.modifiers.remove(m)
    old = a.data; a.data = me; bpy.data.meshes.remove(old); bpy.data.meshes.remove(b.data)


def bulb_section(z, clear):
    """Closed plan outline (x, y) of the bulb at height z, grown by a `clear` disc."""
    xa = cup.ray_cast(Vector((200.0, 0.0, z)), Vector((-1, 0, 0)))[0].x
    xb = cup.ray_cast(Vector((-200.0, 0.0, z)), Vector((1, 0, 0)))[0].x
    dx = 0.05
    xs = [xb+dx*i for i in range(int((xa-xb)/dx)+1)]
    hb = []
    for x in xs:
        hit = cup.ray_cast(Vector((x, 50.0, z)), Vector((0, -1, 0)))
        hb.append(hit[0].y if hit[0] is not None else 0.0)
    nk = int(round(clear/dx))+1
    prof = []
    for i in range(-nk, len(xs)+nk):
        x = xb+dx*i
        best = 0.0
        for j in range(max(0, i-nk), min(len(xs), i+nk+1)):
            d = (j-i)*dx
            if abs(d) <= clear:
                best = max(best, hb[j]+math.sqrt(clear*clear-d*d))
        if best > 0:
            prof.append((x, best))
    return [(x, y) for x, y in prof]+[(x, -y) for x, y in reversed(prof)]


report = {"cradles": []}
pk_in = bulb_section(Z_BASE+POCKET_VGAP, POCKET_CLEAR)
pk_out = bulb_section(Z_BASE+POCKET_VGAP, POCKET_CLEAR+CHAMFER)
PK_X = (min(p[0] for p in pk_out), max(p[0] for p in pk_out))
PK_HY = max(abs(p[1]) for p in pk_out)
zk, prof = notch_profile(WALL_X)
_, prof_c = notch_profile(WALL_X, CLEAR+CHAMFER)
prof, prof_c = deepen(prof, FLOOR_HW), deepen(prof_c, FLOOR_HW+CHAMFER)
top_b = max(y for y, z in prof if z <= Z_TOP+1e-6)
arm_out = top_b+ARM
BASE_W = max(BASE_W_MIN, 2*round(arm_out+2.0, 0))
x_lo, x_hi = min(PK_X[0]-BASE_MARGIN, BULB_TAIL_X-TAIL_MARGIN), WALL_X+PLATE_T/2+BASE_MARGIN
base = rings_solid("Stand", [[(x, y, Z_BASE-BASE_T) for x, y in rrect(x_lo, x_hi, -BASE_W/2, BASE_W/2, BASE_R)],
                             [(x, y, Z_BASE-BASE_CH) for x, y in rrect(x_lo, x_hi, -BASE_W/2, BASE_W/2, BASE_R)],
                             [(x, y, Z_BASE) for x, y in rrect(x_lo+BASE_CH, x_hi-BASE_CH, -BASE_W/2+BASE_CH,
                                                                 BASE_W/2-BASE_CH, BASE_R-BASE_CH)]])
# keel pocket: straight walls (bulb section at the base top + clearance), floor = the bulb flat, chamfered rim
pin, pout = resample(pk_in, NRS), resample(pk_out, NRS)
e = 0.05
pocket = rings_solid("Pocket", [[(x, y, zz) for x, y in ring] for zz, ring in
                                ((z_flat, pin), (Z_BASE-CHAMFER, pin), (Z_BASE+e, pout), (Z_BASE+1.0, pout))])
boolean(base, pocket, "DIFFERENCE")
x0 = WALL_X
r = 1.6
outline = [(-FOOT_HW, Z_BASE-1.0), (FOOT_HW, Z_BASE-1.0)]
outline += [(arm_out-r+r*math.cos(math.radians(a)), Z_TOP-r+r*math.sin(math.radians(a))) for a in range(0, 91, 10)]
outline += [(-(arm_out-r)-r*math.cos(math.radians(a)), Z_TOP-r+r*math.sin(math.radians(a))) for a in range(90, -1, -10)]
plate = prism_x("Wall", outline, x0-PLATE_T/2, x0+PLATE_T/2)
z_cap = Z_TOP+CLEAR+1.0
inner = resample(notch_poly(prof, z_cap), NRS)
outer = resample(notch_poly(prof_c, z_cap+CHAMFER), NRS)
h = PLATE_T/2
cut = rings_solid("Notch", [[(x0+sx, y, z) for y, z in ring] for sx, ring in
                           ((-h-1.0, outer), (-h-e, outer), (-h+CHAMFER-e, inner), (h-CHAMFER+e, inner),
                            (h+e, outer), (h+1.0, outer))])
boolean(plate, cut, "DIFFERENCE")
boolean(base, plate, "UNION")
# clearance audits: wall notch to hull/appendages, pocket wall to the bulb
mind, worst = 99.0, None
for y, z in [q for q in prof if q[1] <= Z_TOP][::2]:
    for sy in (1, -1):
        for x in (x0-PLATE_T/2, x0, x0+PLATE_T/2):
            p = Vector((x, sy*y, z))
            for tree in (hull, app):
                n = tree.find_nearest(p)
                if n[0] is not None and n[3] < mind:
                    mind, worst = n[3], (round(x, 1), round(sy*y, 2), round(z, 2))
wall_gap = (x0-PLATE_T/2)-APP_NOSE_X
report["cradles"].append({"x": round(x0, 2), "hull_bottom_z": round(zk, 2), "notch_top_half_width": round(top_b, 2),
                          "arm_outer_half_width": round(arm_out, 2), "arm_top_z": Z_TOP,
                          "min_clearance_mm": round(mind, 3), "at": worst, "rim_chamfer_mm": CHAMFER,
                          "floor_gap_to_keel_mm": round(zk-prof[0][1], 2), "floor_relief_half_width_mm": FLOOR_HW})
report["wall"] = {"x": round(x0, 2), "thickness_mm": PLATE_T, "gap_to_bulb_nose_mm": round(wall_gap, 2),
                  "width_at_top_mm": round(2*arm_out, 1), "height_mm": round(Z_TOP-(Z_BASE-BASE_T), 1)}
report["pocket"] = {"depth_mm": POCKET_D, "clearance_mm": POCKET_CLEAR, "outline_height_over_base_top_mm": POCKET_VGAP, "rim_chamfer_mm": CHAMFER,
                    "floor_z": round(z_flat, 2), "x": [round(v, 2) for v in PK_X], "half_width": round(PK_HY, 2)}
report["keel_flat"] = {"z": round(z_flat, 2), "x": [round(v, 2) for v in FLAT_X], "half_width": round(FLAT_HY, 2)}
bm = bmesh.new(); bm.from_mesh(base.data)
bmesh.ops.triangulate(bm, faces=list(bm.faces))
nonman = sum(1 for e in bm.edges if not e.is_manifold)
vol = bm.calc_volume(signed=False)
lo = Vector([min(v.co[i] for v in bm.verts) for i in range(3)])
hi = Vector([max(v.co[i] for v in bm.verts) for i in range(3)])
tris = [tuple(v.co.copy() for v in f.verts) for f in bm.faces]
bm.free()


def write_stl(path, ts, off):
    with open(path, "wb") as f:
        f.write(bytes(80)+struct.pack("<I", len(ts)))
        for t in ts:
            a, b, c = [p+off for p in t]
            n = (b-a).cross(c-a)
            n = n.normalized() if n.length > 0 else n
            f.write(struct.pack("<12fH", *n, *a, *b, *c, 0))


write_stl(os.path.join(SOUT, "Stand.stl"), tris, Vector())
bed_off = Vector((128-(lo.x+hi.x)/2, 128-(lo.y+hi.y)/2, -lo.z))
write_stl(os.path.join(SOUT, "Stand-bed.stl"), tris, bed_off)
report.update({"nonmanifold_edges": nonman, "volume_cm3": round(vol/1000, 2),
               "size_mm": [round(hi[i]-lo[i], 1) for i in range(3)], "base_top_z": round(Z_BASE, 2),
               "bulb_gap_mm": 0.0, "plate_thickness_mm": PLATE_T, "clearance_mm": CLEAR,
               "assembled_bbox": [[round(v, 2) for v in lo], [round(v, 2) for v in hi]]})
# true pocket gap: stand surface vertices around the pocket (floor excluded) to the bulb cup, and back
walls = [t for t in tris if max(v.z for v in t) > z_flat+0.005]      # the floor is the intended contact
stree = BVHTree.FromPolygons([v for t in walls for v in t], [(3*i, 3*i+1, 3*i+2) for i in range(len(walls))])
pmin, pworst = 99.0, None
for t in walls:
    for v in t:
        if z_flat+0.01 < v.z <= Z_BASE+0.01 and PK_X[0]-0.5 <= v.x <= PK_X[1]+0.5 and abs(v.y) <= PK_HY+0.5:
            n = cup.find_nearest(v)
            if n[0] is not None and n[3] < pmin:
                pmin, pworst = n[3], (round(v.x, 2), round(v.y, 2), round(v.z, 2))
for v in cv:
    if v.z > z_flat+0.01 and v.z <= Z_BASE+0.5:
        n = stree.find_nearest(v)
        if n[0] is not None and n[3] < pmin:
            pmin, pworst = n[3], (round(v.x, 2), round(v.y, 2), round(v.z, 2))
report["pocket"].update({"min_gap_to_bulb_mm": round(pmin, 3), "at": pworst})
if pmin < 0.25:
    raise RuntimeError("pocket gap %.3f" % pmin)
# ---- stability: boat on the keel flat, then boat + stand on a table ----
cvol, cmom = 0.0, Vector()
for a, b, c in tris:
    v6 = a.dot(b.cross(c))
    cvol += v6; cmom += v6*(a+b+c)/4.0
stand_cg = cmom/cvol
stand_g = vol/1000*PLA_STAND_G_PER_CM3
stand_g_src = "estimate %.3f g/cm3" % PLA_STAND_G_PER_CM3
tt = os.path.join(SOUT, "slice", "times.txt")       # a previous slice of the same geometry gives the real grams
if os.path.exists(tt):
    import re
    mg = re.search(r"total filament weight \[g\] : ([\d.]+)", open(tt).read())
    if mg:
        stand_g, stand_g_src = float(mg.group(1)), "BambuStudio slice"
hj = json.load(open(os.path.join(OUT, "hydro_check.json")))
M, Lm, Lc = hj["mass_g"]["total"], hj["mass_g"]["lead"], Vector(hj["lead_centroid"])
G = Vector(hj["G"])
cases = {"sailing trim (full lead, paper sail)": (M, G),
         "no lead": (M-Lm, (G*M-Lc*Lm)/(M-Lm))}
ds = os.environ.get("DISPLAY_SAIL_JSON")
if ds and os.path.exists(ds):
    dj = json.load(open(ds))
    dm = dj["mass_g"]-dj["replaces_paper_g"]
    cases["full lead, printed display sail"] = (M+dm, (G*M+Vector(dj["centroid"])*dm)/(M+dm))
table_z = Z_BASE-BASE_T
tdx, tdz = TAIL.x-FLAT_X[0], TAIL.z-z_flat           # tail relative to the aft edge of the flat
tail_land = next(a/10 for a in range(0, 900) if tdz*math.cos(math.radians(a/10))+tdx*math.sin(math.radians(a/10)) <= POCKET_D)
stab = {"stand_mass_g_est": round(stand_g, 1), "stand_mass_source": stand_g_src, "stand_cg": [round(v, 2) for v in stand_cg], "cases": {}}
for k, (m, g) in cases.items():
    hgt = g.z-z_flat
    tot = (g*m+stand_cg*stand_g)/(m+stand_g)
    H = tot.z-table_z
    stab["cases"][k] = {
        "boat_mass_g": round(m, 2), "G": [round(v, 2) for v in g],
        "G_margin_to_flat_aft_mm": round(g.x-FLAT_X[0], 2), "G_margin_to_flat_fore_mm": round(FLAT_X[1]-g.x, 2),
        "nose_up_rock_until_tail_lands_deg": round(tail_land, 1),
        "nose_up_tip_deg": round(math.degrees(math.atan2(g.x-TAIL.x, g.z-TAIL.z)), 1),
        "nose_down": "blocked by the wall (%.1f mm ahead of the flat)" % (x0-FLAT_X[1]),
        "assembly_tip_deg": {"sideways": round(math.degrees(math.atan2(BASE_W/2-abs(tot.y), H)), 1),
                             "forward": round(math.degrees(math.atan2(x_hi-tot.x, H)), 1),
                             "aft": round(math.degrees(math.atan2(tot.x-x_lo, H)), 1)}}
    if not (FLAT_X[0]+5.0 < g.x < FLAT_X[1]-5.0):
        raise RuntimeError("G %.2f not inside the keel flat with 5 mm margin" % g.x)
report["stability"] = stab
report["base_mm"] = [round(x_hi-x_lo, 1), BASE_W, BASE_T]
json.dump(report, open(os.path.join(SOUT, "stand.json"), "w"), indent=1)
print("STAND", json.dumps(report))
if nonman:
    raise RuntimeError("stand non-manifold")
