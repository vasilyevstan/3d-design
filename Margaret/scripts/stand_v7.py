"""Minimal display stand for Margaret: a rounded base plank and two upright cradle plates whose notches are the
hull-section envelope (over the plate thickness) grown by a 0.3 mm disc, with a 0.4 mm chamfer on both rims so
no sharp edge touches the paint.  One navy piece, printed upright as-is, no supports.  Run: MARGARET_OUT=<v7 build dir> STAND_OUT=<dir> blender -b --factory-startup -P stand_v7.py
Writes Stand.stl (assembled boat coordinates, mm), Stand-bed.stl (placed on a 256 mm bed) and stand.json."""
import os, json, math, struct, bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

OUT, SOUT = os.environ["MARGARET_OUT"], os.environ["STAND_OUT"]
os.makedirs(SOUT, exist_ok=True)
HULL = ["Lower_blue", "Lower_white", "Lower_ink", "Upper_white", "Upper_ink", "Upper_teak"]
APPENDAGES = ["Fin_cap", "Ballast_cup", "Rudder", "Rudder_ink"]
CRADLE_X = (40.0, -62.0)        # forward of the bulb nose, between bulb tail and rudder
PLATE_T, CLEAR, ARM, Z_TOP = 3.2, 0.3, 3.2, -3.0
CHAMFER, NRS = 0.4, 2000
BASE_T, BASE_W, BASE_R, BASE_CH, BULB_GAP = 4.0, 50.0, 10.0, 0.8, 3.0
FOOT_HW = 13.0


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
z_lowest = min(v.z for v in av)
Z_BASE = z_lowest-BULB_GAP


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


report = {"cradles": []}
x_lo, x_hi = min(CRADLE_X)-9.0, max(CRADLE_X)+9.0
base = rings_solid("Stand", [[(x, y, Z_BASE-BASE_T) for x, y in rrect(x_lo, x_hi, -BASE_W/2, BASE_W/2, BASE_R)],
                             [(x, y, Z_BASE-BASE_CH) for x, y in rrect(x_lo, x_hi, -BASE_W/2, BASE_W/2, BASE_R)],
                             [(x, y, Z_BASE) for x, y in rrect(x_lo+BASE_CH, x_hi-BASE_CH, -BASE_W/2+BASE_CH,
                                                                 BASE_W/2-BASE_CH, BASE_R-BASE_CH)]])
for i, x0 in enumerate(CRADLE_X):
    zk, prof = notch_profile(x0)
    _, prof_c = notch_profile(x0, CLEAR+CHAMFER)
    top_b = max(y for y, z in prof if z <= Z_TOP+1e-6)
    arm_out = top_b+ARM
    r = 1.6
    outline = [(-FOOT_HW, Z_BASE-1.0), (FOOT_HW, Z_BASE-1.0)]
    outline += [(arm_out-r+r*math.cos(math.radians(a)), Z_TOP-r+r*math.sin(math.radians(a))) for a in range(0, 91, 10)]
    outline += [(-(arm_out-r)-r*math.cos(math.radians(a)), Z_TOP-r+r*math.sin(math.radians(a))) for a in range(90, -1, -10)]
    plate = prism_x("Cradle%d" % i, outline, x0-PLATE_T/2, x0+PLATE_T/2)
    z_cap = Z_TOP+CLEAR+1.0
    inner = resample(notch_poly(prof, z_cap), NRS)
    outer = resample(notch_poly(prof_c, z_cap+CHAMFER), NRS)
    h, e = PLATE_T/2, 0.05
    cut = rings_solid("Notch%d" % i, [[(x0+sx, y, z) for y, z in ring] for sx, ring in
                                     ((-h-1.0, outer), (-h-e, outer), (-h+CHAMFER-e, inner), (h-CHAMFER+e, inner),
                                      (h+e, outer), (h+1.0, outer))])
    boolean(plate, cut, "DIFFERENCE")
    boolean(base, plate, "UNION")
    # clearance audit: nearest hull/appendage distance from cradle sample points
    mind, worst = 99.0, None
    for y, z in [q for q in prof if q[1] <= Z_TOP][::2]:
        for sy in (1, -1):
            for x in (x0-PLATE_T/2, x0, x0+PLATE_T/2):
                p = Vector((x, sy*y, z))
                for tree in (hull, app):
                    n = tree.find_nearest(p)
                    if n[0] is not None and n[3] < mind:
                        mind, worst = n[3], (round(x, 1), round(sy*y, 2), round(z, 2))
    report["cradles"].append({"x": x0, "hull_bottom_z": round(zk, 2), "notch_top_half_width": round(top_b, 2),
                              "arm_outer_half_width": round(arm_out, 2), "arm_top_z": Z_TOP,
                              "min_clearance_mm": round(mind, 3), "at": worst,
                              "rim_chamfer_mm": CHAMFER})

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
               "bulb_gap_mm": BULB_GAP, "plate_thickness_mm": PLATE_T, "clearance_mm": CLEAR,
               "assembled_bbox": [[round(v, 2) for v in lo], [round(v, 2) for v in hi]]})
json.dump(report, open(os.path.join(SOUT, "stand.json"), "w"), indent=1)
print("STAND", json.dumps(report))
if nonman:
    raise RuntimeError("stand non-manifold")
