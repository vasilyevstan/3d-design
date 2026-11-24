import bpy, os, sys
from mathutils import Vector
OUTD = os.environ["CLOSE_OUT"]; os.makedirs(OUTD, exist_ok=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"; sc.render.film_transparent = False
hide = os.environ.get("CLOSE_HIDE", "Preview_").split(",")
for o in sc.objects:
    if o.type == "MESH" and any(o.name.startswith(h) for h in hide if h): o.hide_render = True
def cam(eye, target, scale, res):
    d = bpy.data.cameras.new("c"); d.type = "ORTHO"; d.ortho_scale = scale; d.clip_start = 0.1; d.clip_end = 5000
    o = bpy.data.objects.new("c", d); sc.collection.objects.link(o)
    o.location = Vector(eye); o.rotation_euler = (Vector(target)-Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    sc.camera = o; sc.render.resolution_x, sc.render.resolution_y = res
VIEWS = {
 "keel_side": ((0, -400, -40), (-5, 0, -40), 50, (1200, 800)),
 "keel_q": ((-120, -160, -20), (-10, 0, -42), 45, (1200, 800)),
 "stern_q": ((-260, -170, 90), (-88, 0, 6), 46, (1200, 900)),
 "stern_aft": ((-400, 0, 20), (-90, 0, 6), 70, (1200, 700)),
 "stern_side": ((-90, -400, 6), (-88, 0, 6), 40, (1200, 800)),
 "deck_plan": ((0, 0, 600), (0, 0, 0), 215, (1600, 700)),
 "bow_q": ((240, -200, 120), (60, 0, 10), 90, (1200, 900)),
 "foredeck": ((60, 0, 600), (60, 0, 0), 70, (1400, 900)),
 "ladder": ((-140, -60, 60), (-94, 0, 4.5), 22, (1200, 900)),
 "anchor_q": ((190, -150, 90), (97, 0, 18), 17, (1200, 900)),
 "anchor_side": ((97, -400, 18), (97, 0, 18), 15, (1200, 900)),
 "anchor_front": ((400, 0, 30), (97, 0, 18), 15, (1200, 900)),
}
for k in os.environ.get("CLOSE_VIEWS", ",".join(VIEWS)).split(","):
    cam(*VIEWS[k]); sc.render.filepath = os.path.join(OUTD, k + ".png")
    bpy.ops.render.render(write_still=True)
print("CLOSEUPS OK")
