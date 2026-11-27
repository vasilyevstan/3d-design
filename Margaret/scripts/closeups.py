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
 "masthead": ((140, -260, 300), (23.5, 0, 237.5), 14, (1200, 900)),
 "masthead_side": ((23.5, -400, 237.5), (23.5, 0, 237.5), 11, (1200, 900)),
 # rev 18: furler J-tang seated in the masthead slot behind the lip, seen from forward and above
 "masthead_fwd": ((110, -70, 300), (24.0, 0, 238.0), 9, (1200, 900)),
 "chainplate": ((80, -150, 75), (22.9, -26.0, 19.0), 14, (1200, 900)),
 "cleat_mid": ((-10, -120, 70), (-34.3, -25.0, 17.5), 12, (1200, 900)),
 "cleat_bow": ((120, -90, 80), (78.4, -9.0, 20.5), 12, (1200, 900)),
 # rev 17: cleats at the bow, spring (max beam) and quarter stations, next to the toe rail; the gooseneck lashing
 "cleat_bow17": ((115, -95, 80), (74.2, -15.4, 20.0), 14, (1200, 900)),
 "cleat_spring": ((25, -120, 70), (-9.5, -29.5, 18.0), 14, (1200, 900)),
 "cleat_quarter": ((-50, -125, 75), (-86.1, -26.0, 17.5), 14, (1200, 900)),
 "deck_cleats": ((0, 0, 600), (-5, -10, 0), 215, (1600, 800)),
 "gooseneck": ((-20, -70, 60), (21.0, 0, 43.5), 12, (1200, 900)),
 "stern_rail": ((-250, -160, 110), (-80, -10, 18), 50, (1200, 900)),
 "rail_side": ((0, -500, 30), (0, 0, 20), 215, (1800, 500)),
 "rail_q": ((150, -260, 120), (10, -20, 18), 120, (1400, 900)),
 "pulpit": ((180, -130, 80), (85, -5, 22), 40, (1200, 900)),
 "stemhead": ((190, -170, 100), (90.5, 0, 21.5), 13, (1200, 900)),
 "rig_front": ((500, 0, 125), (22, 0, 125), 250, (900, 1400)),
 "rig_q": ((330, -330, 190), (40, 0, 110), 270, (1100, 1300)),
}
for k in os.environ.get("CLOSE_VIEWS", ",".join(VIEWS)).split(","):
    cam(*VIEWS[k]); sc.render.filepath = os.path.join(OUTD, k + ".png")
    bpy.ops.render.render(write_still=True)
print("CLOSEUPS OK")
