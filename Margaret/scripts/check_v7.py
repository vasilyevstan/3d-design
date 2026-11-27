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

# 2b printed rig: the shroud frame's tabs drop into the chainplate pockets and the display furler sits in the
# stemhead pocket with its tang in the masthead slot (rev18); none may touch the hull except through clearance gaps
rig = st["rig"]
shr = load("Shrouds"); sbm = bm_of(shr)
low = [v for v in sbm.verts if v.z < max(c["top_z"] for c in rig["chainplates"])+3.0]
d, n, p = min_dist(low, hull_trees, 3.0)
res["shrouds"] = {"triangle_overlaps": overlaps(sbm, hull_trees), "foot_and_tab_min_gap_mm": round(d, 3),
                  "nearest_part": n, "at": p}
fur = load("Furler"); fbm = bm_of(fur)
mtree0 = {"Mast": tree(bm_of(load("Mast")))}
head = [v for v in fbm.verts if v.z > st["furler"]["slot"]["z0"]-3.0]    # tang + head body
d, n, p = min_dist(head, mtree0, 3.0)
dbm = bm_of(load("Furler_ink"))              # drum + foot tab (navy) sit in the stemhead pocket
d2, n2, p2 = min_dist(dbm.verts, hull_trees, 3.0)
res["furler"] = {"hull_overlaps": overlaps(fbm, hull_trees), "mast_overlaps": overlaps(fbm, mtree0),
                 "drum_overlaps": overlaps(dbm, hull_trees),
                 "tang_min_gap_to_mast_mm": round(d, 3), "tang_at": p,
                 "drum_tab_min_gap_to_hull_mm": round(d2, 3), "foot_at": p2}


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

rail_trees = {}
if isinstance(st.get("railings"), dict):
    # 2c rev 11 railings: every tab sits in an open pocket (lateral clearance, floor contact allowed); the fences
    # clear the deck, toe rail and fittings above the pads and do not hit the wheels, rig or furler
    rl = st["railings"]
    rail_bm = {n: bm_of(load(n)) for n in ("Rail_Port", "Rail_Starboard", "RailAft_Port", "RailAft_Starboard")}
    rail_trees = {n: tree(m) for n, m in rail_bm.items()}
    posts = [(x, rl["pads"][k]["pad_top"]) for x, k in zip(rl["posts_x"], [str(v) for v in rl["posts_x_prescale"]])]
    RD = rl["pocket"][3]


    def inside_hull(p):
        best = None
        for t in hull_trees.values():
            h = t.find_nearest(p, 3.0)
            if h[0] is not None and (best is None or h[3] < best[3]):
                best = h
        return best is not None and (p-best[0]).dot(best[1]) < 0


    rail_res = {}
    for n, m in rail_bm.items():
        if n.startswith("RailAft"):
            sgn = 1 if n.endswith("Port") else -1
            legs = [(sgn*y, pt) for y, pt in zip(rl["returns"]["legs_y"], rl["returns"]["pad_tops"])]
            foot_of = lambda v: min(legs, key=lambda L: abs(v.y-L[0]))[1]
        else:
            foot_of = lambda v: min(posts, key=lambda P: abs(v.x-P[0]))[1]
        tabs = [v for v in m.verts if abs(v.z-(foot_of(v)-RD)) < 0.03]
        body = [v for v in m.verts if v.z > foot_of(v)+0.5]
        floor_ok = all(v.z > foot_of(v)-RD-0.03 for v in m.verts)
        # the tab corners at mid-depth must be in air (an open pocket) with a lateral gap; the tab foot rests on the floor
        mids = [Vector((v.x, v.y, foot_of(v)-RD/2)) for v in tabs]
        dt, nt, pt = min_dist(mids, hull_trees, 1.0)
        df, _, _ = min_dist(tabs, hull_trees, 1.0)
        db, nb, pb = min_dist(body, hull_trees, 3.0)
        buried = sum(1 for p in mids if inside_hull(p))
        rail_res[n] = {"tab_vertices": len(tabs), "tab_min_side_gap_mm": round(dt, 3), "tab_nearest": nt, "tab_at": pt,
                       "tab_points_buried": buried, "tab_bottom_not_below_floor": floor_ok,
                       "tab_foot_to_floor_mm": round(df, 3),
                       "fence_min_gap_above_pads_mm": round(db, 3), "fence_nearest": nb, "fence_at": pb}
    others = {"Wheel_Port": tree(bm_of(bpy.data.objects["Wheel_Port"])),
              "Wheel_Starboard": tree(bm_of(bpy.data.objects["Wheel_Starboard"])),
              "Shrouds": tree(sbm), "Furler": tree(fbm), "Mast": mtree0["Mast"]}
    for n, m in rail_bm.items():
        d, on, p = min_dist(m.verts, others, 6.0)
        rail_res[n]["min_gap_to_rig_wheels_mm"] = round(d, 3); rail_res[n]["rig_nearest"] = on
        rail_res[n]["rig_overlaps"] = overlaps(m, others)
    res["railings"] = rail_res
else:
    res["railings"] = "removed in rev 12"

# 3 boom swing about the gooseneck thread loop
mast = bpy.data.objects["Mast"]; mtree = {"Mast": tree(bm_of(mast)), "Shrouds": tree(sbm), **rail_trees}
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
