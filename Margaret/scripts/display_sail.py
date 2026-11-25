"""Optional printed DISPLAY mainsail for Margaret (white + navy PLA, flat on the bed, one-sided relief).
Same outline and tie holes as the full paper sail, so it ties on the same way.  Display only: it weighs ~10x the
paper sail and sits high, so sail on the water with the paper sails.
Markings (sail_marks.py, same as the paper PDF): sail number "MGT 43" on both faces, staggered (starboard higher), each
reading correctly from its own side - port set as a first-layer navy inlay in the bed face, starboard set as a one-layer
navy relief; a full-thickness navy wave insignia near the head; two reef rows (white relief cringle and reef-point patches).
Run: MARGARET_OUT=<v7 build dir> SAIL_OUT=<dir> blender -b --factory-startup -P display_sail.py
Writes Display_sail.stl + Display_sail_ink.stl (assembled boat coordinates, mm), Display_sail-bed.stl +
Display_sail_ink-bed.stl (flat, relief up, with three 0.2 mm mouse ears at head, tack and clew that keep the thin corners
down; snip them off) and display_sail.json."""
import os, sys, json, math, struct, bpy, bmesh
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sail_marks

OUT, SOUT = os.environ["MARGARET_OUT"], os.environ["SAIL_OUT"]
os.makedirs(SOUT, exist_ok=True)
ST = json.load(open(os.path.join(OUT, "stats.json")))
S = ST["sails"]["full"]
L, F = S["luff_mm"], S["foot_mm"]
LUFF_X, TACK_Z = ST["sail"]["luff_x"], ST["sail"]["tack_z"]
AVOID, HOUNDS_Z = ST["luff_tie_z_avoid"], ST["rig"]["hounds_z"]
TAB_W, TAB_H = 4.5, 5.0                         # head tab, as on the paper template
T, RELIEF, BATTEN = 0.52, 0.16, 0.32            # 0.2 + 2 x 0.16 layers; relief one / two layers
INK = 0.2                                       # port-face inlay depth = the 0.2 mm first layer
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
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
MK = sail_marks.layout(L, F)
# reef rows: cringle patches at luff and leech, reef-point patches between them (white relief layer 1)
reef = None
for r in MK["reefs"]:
    pieces = [clipped("cringle", sail_marks.circle(r["luff"], r["patch_r"], 40), Y1+e, Y1-RELIEF),
              clipped("cringle", sail_marks.circle(r["leech"], r["patch_r"], 40), Y1+e, Y1-RELIEF)]
    pieces += [prism("reefpt", sail_marks.circle(p, r["point_r"], 16), Y1+e, Y1-RELIEF) for p in r["points"]]
    for ob in pieces:
        if reef is None:
            reef = ob
        else:
            boolean(reef, ob, "UNION")
boolean(r1, reef, "UNION")
# relief layer 2: four batten pockets square to the leech, between the seams
battens = []
for k, f in enumerate((0.2, 0.4, 0.6, 0.8)):
    q = (C[0]+dl[0]*ll*f, C[1]+dl[1]*ll*f)
    chord = q[0]
    blen = min(18.0, 0.32*chord) if k < 3 else min(12.0, 0.45*chord)
    battens.append((q, blen))
    ob = clipped("batten%d" % k, strip((q[0]-di[0]*0.5, q[1]-di[1]*0.5), di, blen, BATTEN_W), Y1+e, Y1-BATTEN)
    boolean(r1, ob, "UNION")
# ---- navy markings ----
FONT = bpy.data.fonts.load(FONT_PATH)


def glyph_bm(s):
    """Extruded Arial Bold text as a bmesh: x along the line (advance-centred), y up from the baseline, z -0.5..0.5."""
    cu = bpy.data.curves.new("txt", "FONT"); cu.body = s; cu.font = FONT; cu.size = 1.0
    cu.align_x = "CENTER"; cu.extrude = 0.5; cu.resolution_u = 10
    ob = bpy.data.objects.new("txt", cu); bpy.context.scene.collection.objects.link(ob)
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(ob, do_unlink=True); bpy.data.curves.remove(cu)
    bm = bmesh.new(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    return bm


_h = glyph_bm("H")
H_BASE, H_CAP = min(v.co.y for v in _h.verts), max(v.co.y for v in _h.verts)-min(v.co.y for v in _h.verts)
Z_LO, Z_HI = min(v.co.z for v in _h.verts), max(v.co.z for v in _h.verts)
_h.free()


def text_obj(name, s, uc, vb, cap, mirror, y0, y1):
    """Text line between the planes y0, y1; reads +u (port view) or -u when mirror (starboard view)."""
    bm = glyph_bm(s)
    sc = cap/H_CAP
    for vt in bm.verts:
        x, y, z = vt.co
        u = uc-x*sc if mirror else uc+x*sc
        vt.co = Vector(to3(u, vb+(y-H_BASE)*sc, y0+(z-Z_LO)/(Z_HI-Z_LO)*(y1-y0)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob


def number_set(n, y0, y1, tag):
    obs = [text_obj("%s%d" % (tag, i), s, n["uc"], vb, n["cap"], n["mirror"], y0, y1) for i, (s, vb) in enumerate(n["lines"])]
    for ob in obs[1:]:
        boolean(obs[0], ob, "UNION")
    return obs[0]


def merged(name, obs):
    bm = bmesh.new()
    for ob in obs:
        bm.from_mesh(ob.data)
        bpy.data.objects.remove(ob, do_unlink=True)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob


NP, NS = (next(n for n in MK["numbers"] if n["face"] == f) for f in ("port", "starboard"))
BANDS = [b[::-1] if area(b) < 0 else b for b in MK["insignia"]["bands"]]
NUM_PATCH = 0.6                                     # seams/relief stop this far short of each starboard number line


def line_patch(n, m, y0, y1):
    """Rounded rectangle round each line of a number set (the number reads as a sticker panel over the seams)."""
    patch = None
    for i, (s, vb) in enumerate(n["lines"]):
        t = text_obj("np%d" % i, s, n["uc"], vb, n["cap"], n["mirror"], y0, y1)
        us = [LUFF_X-v.co.x for v in t.data.vertices]
        vs = [v.co.z-TACK_Z for v in t.data.vertices]
        bpy.data.objects.remove(t, do_unlink=True)
        u0, u1, v0, v1 = min(us)-m, max(us)+m, min(vs)-m, max(vs)+m
        poly = []
        for cu, cv, a0 in ((u1-m, v0+m, -90), (u1-m, v1-m, 0), (u0+m, v1-m, 90), (u0+m, v0+m, 180)):
            poly += [(cu+m*math.cos(math.radians(a0+90*k/8)), cv+m*math.sin(math.radians(a0+90*k/8))) for k in range(9)]
        ob = prism("np%d" % i, poly, y0, y1)
        if patch is None:
            patch = ob
        else:
            boolean(patch, ob, "UNION")
    return patch


# starboard number replaces the white relief under and round it (a sticker over the seams), then the relief joins
boolean(r1, line_patch(NS, NUM_PATCH, Y1+2*e, Y1-BATTEN-e), "DIFFERENCE")
boolean(r1, number_set(NS, Y1+2*e, Y1-RELIEF-e, "cut_s"), "DIFFERENCE")
boolean(sail, r1, "UNION")
# insignia: navy right through the cloth (and any relief over it); port number: navy first layer of the bed face
boolean(sail, merged("cut_i", [prism("band", b, Y0+0.1, Y1-BATTEN-0.1) for b in BANDS]), "DIFFERENCE")
boolean(sail, number_set(NP, Y0+0.1, Y0-INK, "cut_p"), "DIFFERENCE")
ink = merged("Display_sail_ink", [number_set(NP, Y0, Y0-INK, "port"), number_set(NS, Y1, Y1-RELIEF, "stbd")]
             + [prism("band", b, Y0, Y1) for b in BANDS])
tst_a = sail.copy(); tst_a.data = sail.data.copy(); bpy.context.scene.collection.objects.link(tst_a)
tst_b = ink.copy(); tst_b.data = ink.data.copy(); bpy.context.scene.collection.objects.link(tst_b)
boolean(tst_a, tst_b, "INTERSECT")
_bm = bmesh.new(); _bm.from_mesh(tst_a.data); OVERLAP = _bm.calc_volume(signed=False); _bm.free()
bpy.data.objects.remove(tst_a, do_unlink=True)
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
nm_ink, vol_ink, tris_ink = mesh_tris(ink)
nonman += nm_print+nm_ink
cvol, cmom = 0.0, Vector()
for a, b, c in tris+tris_ink:
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
write_stl(os.path.join(SOUT, "Display_sail_ink.stl"), tris_ink, lambda p: p)
rot = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))     # port face down on the bed, relief up
pts = [rot @ v for t in tris_print for v in t]
lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
off = Vector((128-(lo.x+hi.x)/2, 128-(lo.y+hi.y)/2, -lo.z))
write_stl(os.path.join(SOUT, "Display_sail-bed.stl"), tris_print, lambda p: rot @ p+off)
write_stl(os.path.join(SOUT, "Display_sail_ink-bed.stl"), tris_ink, lambda p: rot @ p+off)
ink_lo = min((rot @ v).z+off.z for t in tris_ink for v in t)


def mark(n):
    return {"face": n["face"], "reads": "mirrored in the port view" if n["mirror"] else "normally from port",
            "text": [s for s, _ in n["lines"]], "cap_mm": round(n["cap"], 2),
            "u_mm": [round(x, 1) for x in n["u_range"]], "v_mm": [round(x, 1) for x in n["v_range"]]}


rep = {"nonmanifold_edges": nonman, "volume_cm3": round((vol+vol_ink)/1000, 3), "mass_g": round((vol+vol_ink)/1000*PLA, 2),
       "white_volume_cm3": round(vol/1000, 3), "ink_volume_cm3": round(vol_ink/1000, 4),
       "ink_mass_g": round(vol_ink/1000*PLA, 3), "white_ink_overlap_mm3": round(OVERLAP, 4),
       "replaces_paper_g": PAPER_G, "centroid": [round(v, 2) for v in cg], "area_cm2": round(area(OUTLINE)/100, 2),
       "luff_mm": round(L, 2), "foot_mm": round(F, 2), "thickness_mm": T, "relief_mm": RELIEF, "batten_relief_mm": BATTEN,
       "relief_face": "starboard", "seams": len(parts), "seam_free_margin_round_starboard_number_mm": NUM_PATCH, "battens": [round(b, 1) for _, b in battens],
       "markings": {"font": os.path.basename(FONT_PATH), "code": MK["code"], "number": MK["number"],
                    "port": dict(mark(NP), layer="navy inlay, first 0.2 mm layer of the bed face"),
                    "starboard": dict(mark(NS), layer="navy relief, one 0.16 mm layer on the relief face"),
                    "insignia": {"type": "two symmetric waves, navy through the full thickness",
                                 "u_mm": round(MK["insignia"]["uc"], 1), "v_mm": round(MK["insignia"]["vc"], 1),
                                 "w_mm": round(MK["insignia"]["w"], 2), "h_mm": round(MK["insignia"]["h"], 2)},
                    "reefs": [{"v_mm": round(r["v"], 1), "points": len(r["points"]), "patch_r_mm": r["patch_r"]}
                              for r in MK["reefs"]],
                    "ink_on_bed": abs(ink_lo) < 1e-3},
       "holes": [{"name": n, "u": round(u, 2), "v": round(v, 2), "d": 2*r} for (u, v), r, n in HOLES],
       "bed_size_mm": [round(hi[i]-lo[i], 2) for i in range(3)],
       "mouse_ears": {"d_mm": 2*EAR_R, "t_mm": EAR_T, "at": ["tack", "clew", "head"], "print_only": True,
                      "mass_g": round((vol_print-vol)/1000*PLA, 2)}}
json.dump(rep, open(os.path.join(SOUT, "display_sail.json"), "w"), indent=1)
print("DISPLAY SAIL", json.dumps(rep))
if nonman:
    raise RuntimeError("display sail non-manifold")
if OVERLAP > 1e-3 or vol_ink < 10.0:
    raise RuntimeError("navy markings: overlap %.4f mm3, volume %.2f mm3" % (OVERLAP, vol_ink))
