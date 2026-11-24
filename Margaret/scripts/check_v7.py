"""Assembled-geometry clearance checks for Margaret v7 (run in Blender with MARGARET_OUT)."""
import os, json, math, bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

OUT = os.environ["MARGARET_OUT"]
st = json.load(open(os.path.join(OUT, "stats.json")))
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob)


def load(name):
    bpy.ops.wm.stl_import(filepath=os.path.join(OUT, name+".stl"))
    ob = bpy.context.selected_objects[0]
    ob.name = name
    return ob


class M:
    def __init__(self, ob, mat=None):
        me = ob.data
        self.verts = [(mat @ v.co) if mat is not None else v.co.copy() for v in me.vertices]
        self.tris = [tuple(p.vertices) for p in me.polygons]


def bm_of(ob, mat=None):
    return M(ob, mat)


def tree(m):
    return BVHTree.FromPolygons(m.verts, m.tris)


hull_names = ["Lower_blue", "Lower_white", "Lower_ink", "Upper_white", "Upper_ink", "Upper_teak", "Window_ink"]
hull = {n: load(n) for n in hull_names}
hull_trees = {n: tree(bm_of(o)) for n, o in hull.items()}
res = {}


def min_dist(points, trees, cap=5.0):
    best = (cap, None, None)
    for p in points:
        for n, t in trees.items():
            hit = t.find_nearest(p, cap)
            if hit[0] is not None and hit[3] < best[0]:
                best = (hit[3], n, tuple(round(c, 2) for c in p))
    return best


def overlaps(bm_a, trees):
    ta = tree(bm_a)
    return {n: len(ta.overlap(t)) for n, t in trees.items() if ta.overlap(t)}


# 1 rudder blade vs hull (stock passes through its bore)
rud = load("Rudder"); rbm = bm_of(rud)
rx = st["rudder_x"]
blade = [v for v in rbm.verts if math.hypot(v.x-rx, v.y) > 1.2]
d, n, p = min_dist(blade, hull_trees)
res["rudder"] = {"blade_min_gap_mm": round(d, 3), "nearest_part": n, "at": p,
                 "triangle_overlaps": overlaps(rbm, hull_trees)}

# 2 wheels vs binnacles/deck (stub sits in its bore)
for wn in ("Wheel_Port", "Wheel_Starboard"):
    w = load(wn); wbm = bm_of(w)
    wx, wy, wz = st["wheel"]["x"], (1 if wn.endswith("Port") else -1)*st["wheel"]["y"], st["wheel"]["z"]
    rim = [v for v in wbm.verts if math.hypot(v.y-wy, v.z-wz) > 1.3]
    d, n, p = min_dist(rim, hull_trees)
    res[wn] = {"rim_min_gap_mm": round(d, 3), "nearest_part": n, "triangle_overlaps": overlaps(wbm, hull_trees)}

for wn in ("WheelSpokes_Port", "WheelSpokes_Starboard"):
    res[wn] = {"triangle_overlaps": overlaps(bm_of(load(wn)), hull_trees)}
res["Rudder_ink_overlaps"] = overlaps(bm_of(load("Rudder_ink")), hull_trees)

# 2b shroud geometry: spreader tip holes must sit outboard of the straight hounds->chainplate line
rig = st["rig"]
hz = rig["hounds_z"]
geo = {}
for py in (1, -1):
    pad = [p for p in rig["padeye_holes"] if p[1]*py > 5][0]
    for sp in rig["spreaders"]:
        zsp, half = sp[0], sp[1]
        y_line = 0.85+(abs(pad[1])-0.85)*(hz-zsp)/(hz-pad[2])
        geo["%s z%.0f" % ("port" if py > 0 else "stbd", zsp)] = {"tip_hole_y": round(half-1.15, 2),
                                                                  "straight_line_y": round(y_line, 2),
                                                                  "deflection_mm": round(half-1.15-y_line, 2)}
res["shroud_deflection"] = geo


def islands(name):
    ob = bpy.data.objects.get(name) or load(name)
    me = ob.data
    parent = list(range(len(me.vertices)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for e in me.edges:
        a, b = find(e.vertices[0]), find(e.vertices[1])
        if a != b:
            parent[a] = b
    comp = {}
    for v in me.vertices:
        comp.setdefault(find(v.index), []).append(v.co)
    small = []
    for c in comp.values():
        ext = [max(p[k] for p in c)-min(p[k] for p in c) for k in range(3)]
        if max(ext) < 0.6 or sorted(ext)[1] < 0.12:
            small.append({"at": [round(sum(p[k] for p in c)/len(c), 2) for k in range(3)],
                          "extent": [round(e, 3) for e in ext]})
    return {"components": len(comp), "tiny": small[:8], "tiny_count": len(small)}


res["islands"] = {n: islands(n) for n in ("Lower_ink", "Upper_ink", "Upper_teak", "Window_ink", "Lower_white",
                                          "Rudder_ink", "WheelSpokes_Port")}

# 3 boom swing about the gooseneck thread loop
mast = load("Mast"); mtree = {"Mast": tree(bm_of(mast))}
boom = load("Boom")
px = st["rig"]["boom_holes_x"]["gooseneck loop"]
swing = {}
for ang in range(-45, 50, 5):
    m = Matrix.Translation((px, 0, 0)) @ Matrix.Rotation(math.radians(ang), 4, "Z") @ Matrix.Translation((-px, 0, 0))
    bbm = bm_of(boom, m)
    d, _, _ = min_dist(bbm.verts, {**mtree, "Upper_white": hull_trees["Upper_white"]}, 3.0)
    ov = overlaps(bbm, {**mtree, "Upper_white": hull_trees["Upper_white"]})
    swing[ang] = {"min_gap": round(d, 3), "overlaps": ov}
res["boom_swing"] = swing
res["boom_free_range_deg"] = [min(a for a, v in swing.items() if not v["overlaps"]),
                              max(a for a, v in swing.items() if not v["overlaps"])]

# 4 mast heel in socket
res["mast_vs_hull_overlaps"] = overlaps(bm_of(mast), hull_trees)
d, n, p = min_dist([v for v in bm_of(mast).verts if v.z < 2.0], hull_trees, 2.0)
res["mast_heel_min_gap"] = {"gap": round(d, 3), "part": n, "at": p}

# 5 bulb cup vs fin cap
cap = load("Fin_cap"); cup = load("Ballast_cup")
mc, mk = bm_of(cup), bm_of(cap)
zsplit = st["bulb"]["split_z"]
pairs = tree(mc).overlap(tree(mk))
off = [(a, b) for a, b in pairs
       if not all(abs(mc.verts[i].z-zsplit) < 0.02 for i in mc.tris[a])
       or not all(abs(mk.verts[i].z-zsplit) < 0.02 for i in mk.tris[b])]
res["cup_cap_overlaps"] = {"total": len(pairs), "off_split_plane": len(off),
                           "examples": [[tuple(round(c, 2) for c in mc.verts[mc.tris[a][0]]),
                                         tuple(round(c, 2) for c in mk.verts[mk.tris[b][0]])] for a, b in off[:4]]}
mod = cup.modifiers.new("ix", "BOOLEAN"); mod.operation = "INTERSECT"; mod.object = cap; mod.solver = "EXACT"
ev = cup.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
bmx = bmesh.new(); bmx.from_mesh(me); res["cup_cap_intersection_mm3"] = round(abs(bmx.calc_volume()), 4); bmx.free()
ev.to_mesh_clear(); cup.modifiers.remove(mod)
res["keel_vs_hull_overlaps"] = overlaps(bm_of(cap), hull_trees)
hb_ = hull["Lower_blue"]
mod = cap.modifiers.new("kx", "BOOLEAN"); mod.operation = "INTERSECT"; mod.object = hb_; mod.solver = "EXACT"
ev = cap.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
bmx = bmesh.new(); bmx.from_mesh(me); res["keel_hull_intersection_mm3"] = round(abs(bmx.calc_volume()), 4); bmx.free()
ev.to_mesh_clear(); cap.modifiers.remove(mod)

print("CHECK", json.dumps(res, indent=1))
json.dump(res, open(os.path.join(OUT, "checks.json"), "w"), indent=1)
