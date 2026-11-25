"""Optional printed DISPLAY mainsail for Margaret (white PLA, flat on the bed, one-sided relief).
Same outline and tie holes as the full paper sail, so it ties on with the same thread.  Display only: it weighs ~10x the
paper sail and sits high, so sail on the water with the paper sails.
Run: MARGARET_OUT=<v7 build dir> SAIL_OUT=<dir> blender -b --factory-startup -P display_sail.py
Writes Display_sail.stl (assembled boat coordinates, mm), Display_sail-bed.stl (flat, relief up, with three 0.2 mm
mouse ears at head, tack and clew that keep the thin corners down; snip them off) and display_sail.json."""
import os, json, math, struct, bpy, bmesh
from mathutils import Vector, Matrix

OUT, SOUT = os.environ["MARGARET_OUT"], os.environ["SAIL_OUT"]
os.makedirs(SOUT, exist_ok=True)
ST = json.load(open(os.path.join(OUT, "stats.json")))
S = ST["sails"]["full"]
L, F = S["luff_mm"], S["foot_mm"]
LUFF_X, TACK_Z = ST["sail"]["luff_x"], ST["sail"]["tack_z"]
AVOID, HOUNDS_Z = ST["luff_tie_z_avoid"], ST["rig"]["hounds_z"]
TAB_W, TAB_H = 4.5, 5.0                         # head tab, as on the paper template
T, RELIEF, BATTEN = 0.52, 0.16, 0.32            # 0.2 + 2 x 0.16 layers; relief one / two layers
TABLING, SEAM_W, SEAM_STEP, BATTEN_W = 1.2, 0.6, 24.0, 1.4
PLA = 1.24
PAPER_G = 0.5                                   # the paper sail it replaces (already in the 64 g budget)
EAR_R, EAR_T = 5.0, 0.2                         # print-only mouse ears (one first layer)

zl = L*(1-TAB_W/F)
OUTLINE = [(0.0, 0.0), (F, 0.0), (TAB_W, zl), (TAB_W, L+TAB_H), (0.0, L+TAB_H)]   # (u aft along the foot, v up the luff)


def ties():
    out, z = [], TACK_Z+14.0
    while z < TACK_Z+L-9.0 and z < HOUNDS_Z-8.0:
        bad = next((a for a in AVOID if a[0]-2.0 <= z <= a[1]+2.0), None)
        if bad:
            z = bad[1]+3.0
            continue
        out.append(z); z += 20.0
    return out


HOLES = [((2.2, L+2.5), 0.6, "head"), ((2.2, 3.0), 0.6, "tack"), ((F-4.0, 2.5), 0.6, "clew")]
HOLES += [((2.0, z-TACK_Z), 0.5, "luff") for z in ties()]


def inset(poly, d):
    """Miter offset of a CCW polygon by d (inwards)."""
    n = len(poly)
    lines = []
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i+1) % n]
        dx, dy = x1-x0, y1-y0
        k = math.hypot(dx, dy)
        nx, ny = -dy/k, dx/k
        lines.append(((x0+nx*d, y0+ny*d), (dx, dy)))
    out = []
    for i in range(n):
        (p, r), (q, s) = lines[i-1], lines[i]
        den = r[0]*s[1]-r[1]*s[0]
        t = ((q[0]-p[0])*s[1]-(q[1]-p[1])*s[0])/den
        out.append((p[0]+t*r[0], p[1]+t*r[1]))
    return out


def area(poly):
    return 0.5*sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(poly, poly[1:]+poly[:1]))


def to3(u, v, y):
    return (LUFF_X-u, y, TACK_Z+v)


def prism(name, poly, y0, y1):
    """Prism of a (u, v) polygon between the planes y0 and y1 (assembled coordinates)."""
    bm = bmesh.new()
    a = [bm.verts.new(to3(u, v, y0)) for u, v in poly]
    b = [bm.verts.new(to3(u, v, y1)) for u, v in poly]
    n = len(poly)
    for i in range(n):
        bm.faces.new((a[i], a[(i+1) % n], b[(i+1) % n], b[i]))
    bm.faces.new(a); bm.faces.new(list(reversed(b)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob


def boolean(a, b, op):
    m = a.modifiers.new("b", "BOOLEAN"); m.operation = op; m.object = b; m.solver = "EXACT"
    me = bpy.data.meshes.new_from_object(a.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    a.modifiers.remove(m)
    old = a.data; a.data = me; bpy.data.meshes.remove(old)
    bpy.data.objects.remove(b, do_unlink=True)


def strip(p, d, length, w):
    """Rectangle from point p along unit direction d."""
    nx, ny = -d[1], d[0]
    q = (p[0]+d[0]*length, p[1]+d[1]*length)
    return [(p[0]+nx*w/2, p[1]+ny*w/2), (q[0]+nx*w/2, q[1]+ny*w/2), (q[0]-nx*w/2, q[1]-ny*w/2), (p[0]-nx*w/2, p[1]-ny*w/2)]


Y0, Y1 = T/2, -T/2                                 # +y = port (smooth, bed side); relief on starboard (-y)
sail = prism("Display_sail", OUTLINE, Y0, Y1)
e = 0.05
# relief layer 1: tabling round every edge, cross-cut seams, corner patches
inner = inset(OUTLINE, TABLING)
edge = inset(OUTLINE, 0.03)                         # relief stops 0.03 mm inside the edge (no coplanar side faces)
r1 = prism("tabling", edge, Y1+e, Y1-RELIEF)
boolean(r1, prism("tab_in", inner, Y1+2*e, Y1-RELIEF-e), "DIFFERENCE")
C, P = OUTLINE[1], OUTLINE[2]
ll = math.dist(C, P)
dl = ((P[0]-C[0])/ll, (P[1]-C[1])/ll)              # up the leech
di = (-dl[1], dl[0])                                # perpendicular, into the sail (towards the luff)
if di[0] > 0:
    di = (-di[0], -di[1])
parts = []
s = SEAM_STEP*0.75
while s < ll-12.0:
    q = (C[0]+dl[0]*s, C[1]+dl[1]*s)
    parts.append(strip((q[0]-di[0]*2, q[1]-di[1]*2), di, 120.0, SEAM_W))
    s += SEAM_STEP
seams = None
for k, poly in enumerate(parts):
    ob = prism("seam%d" % k, poly, Y1+e, Y1-RELIEF)
    if seams is None:
        seams = ob
    else:
        boolean(seams, ob, "UNION")
boolean(seams, prism("clip", inset(OUTLINE, TABLING-0.15), Y1+2*e, Y1-RELIEF-e), "INTERSECT")
boolean(r1, seams, "UNION")
patches = [[(0.0, 0.0), (13.0, 0.0), (0.0, 13.0)],
           [(F, 0.0), (F-13.0, 0.0), (F+dl[0]*13.0, dl[1]*13.0)],
           [(0.0, L+TAB_H), (TAB_W, L+TAB_H), (TAB_W, zl-2.0), (0.0, L-14.0)]]
edge2 = inset(OUTLINE, 0.08)                        # patches/battens end inside the tabling band


def clipped(name, poly, y0, y1):
    ob = prism(name, poly, y0, y1)
    boolean(ob, prism("c", edge2, y0+e, y1-e), "INTERSECT")
    return ob


for k, poly in enumerate(patches):
    if area(poly) < 0:
        poly = poly[::-1]
    boolean(r1, clipped("patch%d" % k, poly, Y1+e, Y1-RELIEF), "UNION")
# relief layer 2: four batten pockets square to the leech, between the seams
battens = []
for k, f in enumerate((0.2, 0.4, 0.6, 0.8)):
    q = (C[0]+dl[0]*ll*f, C[1]+dl[1]*ll*f)
    chord = q[0]
    blen = min(18.0, 0.32*chord) if k < 3 else min(12.0, 0.45*chord)
    battens.append((q, blen))
    ob = clipped("batten%d" % k, strip((q[0]-di[0]*0.5, q[1]-di[1]*0.5), di, blen, BATTEN_W), Y1+e, Y1-BATTEN)
    boolean(r1, ob, "UNION")
boolean(sail, r1, "UNION")
EARS = [(0.0, 0.0), (F, 0.0), (TAB_W/2, L+TAB_H)]
pr = sail.copy(); pr.data = sail.data.copy(); pr.name = "Display_sail_print"
bpy.context.scene.collection.objects.link(pr)
for k, (u, v) in enumerate(EARS):
    disc = [(u+EAR_R*math.cos(a*math.tau/48), v+EAR_R*math.sin(a*math.tau/48)) for a in range(48)]
    boolean(pr, prism("ear%d" % k, disc, Y0, Y0-EAR_T), "UNION")
# tie holes through everything (and through the ears)
for ob in (sail, pr):
    for (u, v), rad, _ in HOLES:
        poly = [(u+rad*math.cos((a+0.5)*math.tau/24), v+rad*math.sin((a+0.5)*math.tau/24)) for a in range(24)]
        boolean(ob, prism("hole", poly, Y0+1.0, Y1-1.0), "DIFFERENCE")


def mesh_tris(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    nm = sum(1 for ed in bm.edges if not ed.is_manifold)
    for ed in bm.edges:
        if not ed.is_manifold:
            print("NM", ob.name, [tuple(round(c, 3) for c in v.co) for v in ed.verts], len(ed.link_faces))
    vl = bm.calc_volume(signed=False)
    ts = [tuple(v.co.copy() for v in f.verts) for f in bm.faces]
    bm.free()
    return nm, vl, ts


nonman, vol, tris = mesh_tris(sail)
nm_print, vol_print, tris_print = mesh_tris(pr)
nonman += nm_print
cvol, cmom = 0.0, Vector()
for a, b, c in tris:
    v6 = a.dot(b.cross(c)); cvol += v6; cmom += v6*(a+b+c)/4.0
cg = cmom/cvol


def write_stl(path, ts, tf):
    with open(path, "wb") as f:
        f.write(bytes(80)+struct.pack("<I", len(ts)))
        for t in ts:
            a, b, c = [tf(p) for p in t]
            n = (b-a).cross(c-a)
            n = n.normalized() if n.length > 0 else n
            f.write(struct.pack("<12fH", *n, *a, *b, *c, 0))


write_stl(os.path.join(SOUT, "Display_sail.stl"), tris, lambda p: p)
rot = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))     # port face down on the bed, relief up
pts = [rot @ v for t in tris_print for v in t]
lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
off = Vector((128-(lo.x+hi.x)/2, 128-(lo.y+hi.y)/2, -lo.z))
write_stl(os.path.join(SOUT, "Display_sail-bed.stl"), tris_print, lambda p: rot @ p+off)
rep = {"nonmanifold_edges": nonman, "volume_cm3": round(vol/1000, 3), "mass_g": round(vol/1000*PLA, 2),
       "replaces_paper_g": PAPER_G, "centroid": [round(v, 2) for v in cg], "area_cm2": round(area(OUTLINE)/100, 2),
       "luff_mm": round(L, 2), "foot_mm": round(F, 2), "thickness_mm": T, "relief_mm": RELIEF, "batten_relief_mm": BATTEN,
       "relief_face": "starboard", "seams": len(parts), "battens": [round(b, 1) for _, b in battens],
       "holes": [{"name": n, "u": round(u, 2), "v": round(v, 2), "d": 2*r} for (u, v), r, n in HOLES],
       "bed_size_mm": [round(hi[i]-lo[i], 2) for i in range(3)],
       "mouse_ears": {"d_mm": 2*EAR_R, "t_mm": EAR_T, "at": ["tack", "clew", "head"], "print_only": True,
                      "mass_g": round((vol_print-vol)/1000*PLA, 2)}}
json.dump(rep, open(os.path.join(SOUT, "display_sail.json"), "w"), indent=1)
print("DISPLAY SAIL", json.dumps(rep))
if nonman:
    raise RuntimeError("display sail non-manifold")
