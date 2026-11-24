"""Add the display stand to the delivered blend (own collection, not part of the boat plate) and render it.

Run: STAND_DIR=<dir with Stand.stl> MARGARET_WORK=<render dir> blender -b <stage>/Margaret.blend -P stand_show.py
Saves the blend in place and writes stand-1.png (boat on stand), stand-2.png (cradles), stand-3.png (stand alone).
"""
import bpy, os
from mathutils import Vector

SD, WORK = os.environ["STAND_DIR"], os.environ["MARGARET_WORK"]
sc = bpy.context.scene
TITLE = "Display stand (separate print)"
col = bpy.data.collections.get(TITLE)
if col is None:
    col = bpy.data.collections.new(TITLE); sc.collection.children.link(col)
for ob in list(col.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
bpy.ops.wm.stl_import(filepath=os.path.join(SD, "Stand.stl"))
st = bpy.context.selected_objects[0]
st.name = st.data.name = "Display_stand"
for uc in list(st.users_collection):
    uc.objects.unlink(st)
col.objects.link(st)
ink = bpy.data.objects["Upper_ink"].active_material
st.data.materials.clear(); st.data.materials.append(ink)
for p in st.data.polygons:
    p.use_smooth = False
camcol = bpy.data.collections.get("Cameras")


def cam(name, eye, target, scale):
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    d = bpy.data.cameras.new(name); d.type = "ORTHO"; d.ortho_scale = scale; d.clip_start = 0.1; d.clip_end = 5000
    o = bpy.data.objects.new(name, d); (camcol or sc.collection).objects.link(o)
    o.location = Vector(eye); o.rotation_euler = (Vector(target)-Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    return o


c1 = cam("Cam 7 - On the display stand", (300, -330, 120), (-5, 0, 85), 365)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, compress=True)

sc.render.film_transparent = True
shots = [("stand-1", c1, (1200, 1500), set()),
         ("stand-2", cam("tmp2", (230, -300, -10), (-10, 0, -30), 150), (1600, 1000), {"Preview"}),
         ("stand-3", cam("tmp3", (200, -260, 150), (-11, 0, -30), 190), (1600, 1000), {"Print", "Preview"})]
for key, c, res, hide in shots:
    for ch in sc.collection.children:
        ch.hide_render = any(ch.name.startswith(h) for h in hide)
    sc.camera = c
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = os.path.join(WORK, key + ".png")
    bpy.ops.render.render(write_still=True)
print("STAND SHOW OK")
