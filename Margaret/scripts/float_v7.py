"""Render Margaret (transparent film) at the hydro_check equilibrium; presentation_v7 tints the water.
Render Margaret afloat at the hydro_check equilibrium (upright and heeled).
Run: Blender -b stage/Margaret.blend -P float_v7.py   env: MARGARET_OUT (hydro_check.json), FLOAT_OUT (dir)."""
import bpy, os, json, math
from mathutils import Vector

H = json.load(open(os.path.join(os.environ["MARGARET_OUT"], "hydro_check.json")))
OUTD = os.environ["FLOAT_OUT"]; os.makedirs(OUTD, exist_ok=True)
sc = bpy.context.scene
curve = {c["phi"]: c for c in H["curve"]}

pivot = bpy.data.objects.new("FloatPivot", None); sc.collection.objects.link(pivot)
for o in list(sc.objects):
    if o.type in ("MESH", "CURVE") and o.parent is None and o is not pivot:
        o.parent = pivot

sc.render.film_transparent = True


def cam(eye, target, scale, res):
    d = bpy.data.cameras.new("fc"); d.type = "ORTHO"; d.ortho_scale = scale; d.clip_end = 5000
    o = bpy.data.objects.new("fc", d); sc.collection.objects.link(o)
    o.location = Vector(eye); o.rotation_euler = (Vector(target)-Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    sc.camera = o; sc.render.resolution_x, sc.render.resolution_y = res


SHOTS = [("float-upright", 0, (0, -700, 12), (0, 0, 12), 250, (1600, 1000)),
         ("float-heel15", 15, (700, 0, 95), (0, 0, 95), 335, (1100, 1300))]
res = {}
for name, phi, eye, tgt, scale, rs in SHOTS:
    c = curve[phi]
    pivot.rotation_euler = (math.radians(phi), math.radians(c["trim_deg"]), 0)
    pivot.location = (0, 0, c["sink_mm"])
    cam(eye, tgt, scale, rs)
    sc.render.filepath = os.path.join(OUTD, name+".png")
    bpy.ops.render.render(write_still=True)
    W_, H_ = rs
    mm_px = scale/max(W_, H_)
    res[name] = {"waterline_row_px": round(H_/2+(tgt[2]-0.0)/mm_px, 1), "heel_deg": phi, "trim_deg_bow_down": c["trim_deg"], "sink_mm": c["sink_mm"], "GZ_mm": c["GZ_mm"]}
json.dump(res, open(os.path.join(OUTD, "float.json"), "w"), indent=1)
print("FLOAT DONE", res)
