# rev 17 probes: rudder-tube wall continuity (hull skin -> cockpit sole) and the mast seating gauge
import bpy, os, json, math
from mathutils import Vector
OUT = os.environ["MARGARET_OUT"]; st = json.load(open(os.path.join(OUT, "stats.json")))
bpy.ops.wm.read_factory_settings(use_empty=True)
obs = {}
for n in ("Lower_blue", "Lower_white", "Lower_ink", "Upper_white", "Upper_ink", "Upper_teak", "Mast"):
    bpy.ops.wm.stl_import(filepath=os.path.join(OUT, n + ".stl")); obs[n] = bpy.context.selected_objects[0]
dg = bpy.context.evaluated_depsgraph_get()
def inside(o, p):
    ok, loc, nor, _ = o.closest_point_on_mesh(p)
    return ok and (loc - p).dot(nor) > 0
def solid(p): return any(inside(o, p) for k, o in obs.items() if k != "Mast")
def ray_z(o, x, y, z0, d):
    ok, loc, *_ = o.ray_cast(Vector((x, y, z0)), Vector((0, 0, d)))
    return loc.z if ok else None
rx = st["rudder_x"]; res = {"rudder_x": rx}
zb = ray_z(obs["Lower_blue"], rx + 1.7, 0, -60, 1)          # hull underside at the tube wall
holes = []
for r in (1.45, 1.7, 1.95):
    for k in range(16):
        a = 2*math.pi*k/16; x, y = rx + r*math.cos(a), r*math.sin(a)
        zl = ray_z(obs["Lower_blue"], x, y, -60, 1)          # local hull underside on this probe line
        z = zl + 0.15
        while z < 9.55:
            chamfer = r < 1.55 + 0.01 and abs(z - 2.5) < 0.36 and r <= 1.25 + 0.3*(1 - abs(z - 2.5)/0.35) + 0.02
            if abs(z - 2.5) > 0.06 and not chamfer and not solid(Vector((x, y, z))): holes.append((round(r, 2), k, round(z, 2)))
            z += 0.1
res["rudder_tube"] = {"hull_underside_z": round(zb, 2), "probe_top_z": 9.55, "samples_in_air": len(holes), "examples": holes[:8]}
# what is above the tube top: is the bore open to the cockpit sole (not to the cabin)?
res["rudder_bore_top_hit"] = ray_z(obs["Upper_white"], rx, 0, 5.0, 1)
# seating gauge
mx = [v.co.x for v in obs["Mast"].data.vertices if v.co.z < 0]
xa, xf = min(mx), max(mx); xc = 0.5*(xa+xf)
collar = max(filter(None, [ray_z(obs[n], xc, 2.6, 80, -1) for n in ("Upper_white", "Upper_ink", "Upper_teak")]))
heel = min(v.co.z for v in obs["Mast"].data.vertices)
floor = ray_z(obs["Lower_blue"], xc, 0, heel - 0.01, -1) or ray_z(obs["Lower_white"], xc, 0, heel - 0.01, -1)
for n in ("Lower_ink", "Lower_white", "Lower_blue"):
    f = ray_z(obs[n], xc, 0, heel - 0.01, -1)
    if f is not None and f > heel - 2: floor = f; break
res["mast"] = {"heel_x": [round(xa, 2), round(xf, 2)], "collar_top_z": round(collar, 2), "gooseneck_top_z": st.get("gooseneck_z"),
               "seating_gauge_collar_to_saddle_top_mm": round(st.get("gooseneck_z", 43.0) - collar, 2),
               "heel_z": round(heel, 2), "socket_floor_z": None if floor is None else round(floor, 2)}
print("PROBE", json.dumps(res))
json.dump(res, open(os.path.join(OUT, "probe17.json"), "w"), indent=1)
