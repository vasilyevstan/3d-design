"""Add the display stand to the delivered blend (own collection, not part of the boat plate) and render it.

Run: STAND_DIR=<dir with Stand.stl> [SAIL_DIR=<dir with Display_sail.stl>] MARGARET_WORK=<render dir>
     blender -b <stage>/Margaret.blend -P stand_show.py
Saves the blend in place and writes stand-1.png (boat on stand, printed display sail instead of the paper preview sail
when SAIL_DIR is given), stand-2.png (fork on the fin root), stand-3.png (stand alone), stand-4.png
(display sail with its navy markings), stand-5.png (port profile: the neck rising between rudder and keel).
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
white = bpy.data.objects["Upper_white"].active_material
SAIL_TITLE = "Display sail (separate print)"
sail = None
if os.environ.get("SAIL_DIR"):
    scol = bpy.data.collections.get(SAIL_TITLE)
    if scol is None:
        scol = bpy.data.collections.new(SAIL_TITLE); sc.collection.children.link(scol)
    for ob in list(scol.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.ops.wm.stl_import(filepath=os.path.join(os.environ["SAIL_DIR"], "Display_sail.stl"))
    sail = bpy.context.selected_objects[0]
    sail.name = sail.data.name = "Display_sail"
    for uc in list(sail.users_collection):
        uc.objects.unlink(sail)
    scol.objects.link(sail)
    sail.data.materials.clear(); sail.data.materials.append(white)
    for p in sail.data.polygons:
        p.use_smooth = False
    sail.color = (0.93, 0.92, 0.88, 1.0)
    ip = os.path.join(os.environ["SAIL_DIR"], "Display_sail_ink.stl")
    if os.path.exists(ip):                       # navy sail number, insignia and reef rows (second colour)
        bpy.ops.wm.stl_import(filepath=ip)
        si = bpy.context.selected_objects[0]
        si.name = si.data.name = "Display_sail_ink"
        for uc in list(si.users_collection):
            uc.objects.unlink(si)
        scol.objects.link(si)
        si.data.materials.clear(); si.data.materials.append(ink)
        for p in si.data.polygons:
            p.use_smooth = False
        si.color = (0.06, 0.12, 0.28, 1.0)
    scol.hide_render = True                      # off in the boat views; the paper sail is the sailing default
camcol = bpy.data.collections.get("Cameras")


def cam(name, eye, target, scale, roll=0.0):
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    d = bpy.data.cameras.new(name); d.type = "ORTHO"; d.ortho_scale = scale; d.clip_start = 0.1; d.clip_end = 5000
    o = bpy.data.objects.new(name, d); (camcol or sc.collection).objects.link(o)
    q = (Vector(target)-Vector(eye)).to_track_quat("-Z", "Y")
    if roll:
        import math
        from mathutils import Quaternion
        q = q @ Quaternion((0, 0, 1), math.radians(roll))
    o.location = Vector(eye); o.rotation_euler = q.to_euler()
    return o


c1 = cam("Cam 7 - On the display stand", (300, -330, 120), (-5, 0, 85), 365)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, compress=True)

sc.render.film_transparent = True
papers = [o for o in (bpy.data.objects.get(n) for n in ("Preview_PaperSail", "Preview_PaperSail_marks")) if o]
shots = [("stand-1", c1, (1200, 1500), {"Display sail"} if sail is None else set(), sail is not None),
         ("stand-2", cam("tmp2", (200, -300, 30), (-18, 0, -36), 122), (1600, 1000), {"Preview", "Display sail"}, False),
         ("stand-3", cam("tmp3", (140, -240, 150), (-20, 0, -44), 132), (1600, 1000),
          {"Print", "Preview", "Display sail"}, False),
         ("stand-5", cam("tmp5", (-5, -400, -22), (-5, 0, -22), 242), (1600, 640), {"Preview", "Display sail"}, False)]
if sail is not None:
    shots.append(("stand-4", cam("tmp4", (40, -400, 150), (0, 0, 143), 205, roll=90), (1600, 760),
                  {"Print", "Preview", "Display stand"}, False))
before = {ch.name: ch.hide_render for ch in sc.collection.children}
eng = sc.render.engine
for key, c, res, hide, hide_paper in shots:
    if key == "stand-4":                         # relief is 0.16 mm: show it with Workbench cavity shading
        sc.render.engine = "BLENDER_WORKBENCH"
        sh = sc.display.shading
        sh.light, sh.color_type = "STUDIO", "OBJECT"
        sh.show_cavity, sh.cavity_type = True, "BOTH"
        sh.cavity_ridge_factor, sh.cavity_valley_factor = 2.0, 2.0
        sh.curvature_ridge_factor, sh.curvature_valley_factor = 2.0, 2.0
        sh.show_shadows = False
    else:
        sc.render.engine = eng
    for ch in sc.collection.children:
        ch.hide_render = any(ch.name.startswith(h) for h in hide)
    for paper in papers:
        paper.hide_render = hide_paper
    sc.camera = c
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = os.path.join(WORK, key + ".png")
    bpy.ops.render.render(write_still=True)
sc.render.engine = eng
for ch in sc.collection.children:
    ch.hide_render = before[ch.name]
for paper in papers:
    paper.hide_render = False
print("STAND SHOW OK")
