"""Render the printed display sail (white + navy STLs) from port and starboard, Workbench with cavity shading so the
0.16 mm relief reads. Run: SAIL_DIR=<dir> SAIL_IMG=<dir> blender -b --factory-startup -P sail_show.py
Writes sail-port.png and sail-starboard.png (head up, luff towards the bow)."""
import bpy, os, math
from mathutils import Vector

SD, OUT = os.environ["SAIL_DIR"], os.environ["SAIL_IMG"]
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
obs = []
for name, rgb in (("Display_sail", (0.93, 0.92, 0.88, 1)), ("Display_sail_ink", (0.08, 0.16, 0.26, 1))):
    bpy.ops.wm.stl_import(filepath=os.path.join(SD, name + ".stl"))
    ob = bpy.context.selected_objects[0]; ob.name = name
    m = bpy.data.materials.new(name); m.diffuse_color = rgb
    ob.data.materials.append(m); obs.append(ob)
pts = [ob.matrix_world @ Vector(c) for ob in obs for c in ob.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
mid = (lo+hi)/2
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light, sh.color_type = "STUDIO", "MATERIAL"
sh.show_cavity, sh.cavity_type = True, "BOTH"
sh.cavity_ridge_factor = sh.cavity_valley_factor = 2.0
sh.curvature_ridge_factor = sh.curvature_valley_factor = 2.0
sh.show_shadows = False
sc.render.film_transparent = True
sc.render.resolution_x, sc.render.resolution_y = 900, 1800
sc.view_settings.view_transform = "Standard"
for side, sy in (("port", 1), ("starboard", -1)):
    d = bpy.data.cameras.new(side); d.type = "ORTHO"; d.ortho_scale = (hi.z-lo.z)*1.04; d.clip_end = 2000
    c = bpy.data.objects.new(side, d); sc.collection.objects.link(c)
    c.location = Vector((mid.x, sy*300, mid.z))
    c.rotation_euler = (Vector((mid.x, 0, mid.z))-c.location).to_track_quat("-Z", "Y").to_euler()
    sc.camera = c
    sc.render.filepath = os.path.join(OUT, "sail-%s.png" % side)
    bpy.ops.render.render(write_still=True)
print("SAIL SHOW OK")
