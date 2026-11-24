# Transom-name slicing coupons: a 1.06 mm white wall with an inlaid "Margaret" in several variants.
# Writes <name>_white.stl / <name>_ink.stl already placed in bed coordinates + coupons.json.
import os, json, math, bpy, bmesh
from mathutils import Vector, Matrix
OUT = os.environ["COUPON_OUT"]; os.makedirs(OUT, exist_ok=True)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
WALL0, W, H, ZC = 1.06, 16.0, 10.0, 5.5
VB = "/System/Library/Fonts/Supplemental/Verdana Bold.ttf"


def link(name, bm):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob


def box(name, x0, x1, y0, y1, z0, z1):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((x0 if v.co.x < 0 else x1, y0 if v.co.y < 0 else y1, z0 if v.co.z < 0 else z1))
    return link(name, bm)


def boolean(a, b, op, keep=False):
    m = a.modifiers.new("b", "BOOLEAN"); m.operation = op; m.solver = "EXACT"; m.object = b
    me = bpy.data.meshes.new_from_object(a.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    a.modifiers.remove(m); old = a.data; a.data = me; bpy.data.meshes.remove(old)
    if not keep:
        bpy.data.objects.remove(b)


def name_prism(font, size_cap, depth, offset=0.0):
    cu = bpy.data.curves.new("C", "FONT"); cu.body = "Margaret"; cu.font = bpy.data.fonts.load(font)
    cu.size = 1.0; cu.extrude = 1.0; cu.align_x = "CENTER"; cu.resolution_u = 6; cu.offset = offset
    t = bpy.data.objects.new("T", cu); bpy.context.scene.collection.objects.link(t)
    me = bpy.data.meshes.new_from_object(t.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(t)
    bm = bmesh.new(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    X = [v.co.x for v in bm.verts]; Y = [v.co.y for v in bm.verts]
    s = min(size_cap, 14.76/(max(X)-min(X)))
    xc, yc = 0.5*(max(X)+min(X)), 0.5*(max(Y)+min(Y))
    a, b = (depth+1.3)/2, (depth-1.3)/2          # Z=-1 -> x=-1.3 (outboard), Z=+1 -> x=depth (into wall)
    for v in bm.verts:
        Xv, Yv, Zv = v.co
        v.co = Vector((a*Zv+b, W/2-s*(Xv-xc), ZC+s*(Yv-yc)))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return link("Prism", bm), s


VARIANTS = [  # name, size cap, depth, outline offset, rotate face normal to y, wall
    ("A_current", 3.9, 0.6, 0.0, False, 1.06),
    ("B_deep08", 3.9, 0.8, 0.0, False, 1.06),
    ("C_through", 3.9, 1.3, 0.0, False, 1.06),
    ("G_deep08_pad", 3.9, 0.8, 0.0, False, 1.66),
]
info = {}
for i, (nm, cap, depth, off, rot, WALL) in enumerate(VARIANTS):
    wall = box(nm+"_white", 0, WALL, 0, W, 0, H)
    boolean(wall, box("Foot", -3.0, 4.0, 0, W, 0, 1.0), "UNION")
    pr, s = name_prism(VB, cap, depth, off)
    ink = box(nm+"_ink", 0, WALL, 0, W, 0, H)
    boolean(ink, pr, "INTERSECT", keep=True)
    boolean(wall, pr, "DIFFERENCE")
    bx, by = 20+(i % 3)*45, 60+(i//3)*45
    M = Matrix.Translation((bx, by, 0))
    if rot:
        M = M @ Matrix.Rotation(math.radians(90), 4, "Z")
    for ob in (wall, ink):
        ob.data.transform(M)
        for o in bpy.data.objects:
            o.select_set(o is ob)
        bpy.ops.wm.stl_export(filepath=os.path.join(OUT, ob.name+".stl"), export_selected_objects=True)
    P = [M @ Vector(c) for c in ((-0.2, -0.2, 0), (WALL+0.2, W+0.2, H))]
    lo = [min(P[0][k], P[1][k]) for k in range(3)]; hi = [max(P[0][k], P[1][k]) for k in range(3)]
    zz = [v.co.z for v in ink.data.vertices]
    info[nm] = {"size": round(s, 2), "depth": depth, "offset": off, "lo": lo, "hi": hi,
                "ink_z": [round(min(zz), 2), round(max(zz), 2)]}
    print("COUPON", nm, info[nm], flush=True)
json.dump(info, open(os.path.join(OUT, "coupons.json"), "w"), indent=1)
