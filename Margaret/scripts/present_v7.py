"""Organise the v7 blend for delivery and render the presentation views.

Run: Blender -b yacht-build/v7/Margaret.blend -P present_v7.py
Env: MARGARET_OUT (v7 build dir), MARGARET_DELIVER (deliverable dir), MARGARET_WORK (render dir).
"""
import bpy, json, math, os
from mathutils import Vector
from mathutils.bvhtree import BVHTree

OUT, DELIVER, WORK = (os.environ[k] for k in ("MARGARET_OUT", "MARGARET_DELIVER", "MARGARET_WORK"))
os.makedirs(WORK, exist_ok=True)
ST = json.load(open(os.path.join(OUT, "stats.json")))
STAB = json.load(open(os.path.join(OUT, "stability.json")))
sc = bpy.context.scene

GROUPS = {
    "Print - hull and deck": ["Lower_blue", "Lower_white", "Lower_ink", "Upper_white", "Upper_ink", "Upper_teak",
                              "Window_ink"],
    "Print - keel and ballast bulb": ["Fin_cap", "Ballast_cup"],
    "Print - rig": ["Mast", "Boom", "Shrouds", "Furler", "Furler_ink"],
    "Print - steering": ["Rudder", "Rudder_ink", "Wheel_Port", "WheelSpokes_Port", "Wheel_Starboard",
                         "WheelSpokes_Starboard"],
}
cols = {}
for title, names in GROUPS.items():
    c = bpy.data.collections.new(title); sc.collection.children.link(c); cols[title] = c
    for n in names:
        ob = bpy.data.objects.get(n)
        if ob is None:
            continue
        for uc in list(ob.users_collection):
            uc.objects.unlink(ob)
        c.objects.link(ob)
# paper main preview carries the same marks as the PDF/display sail (sail number per face, insignia): reuse the
# display sail's navy marks, thinned from the 0.52 mm print to the 0.24 mm paper preview (render-only decals)
_ink = os.path.join(OUT, "dsail", "Display_sail_ink.stl")
if os.path.exists(_ink) and bpy.data.objects.get("Preview_PaperSail") and not bpy.data.objects.get("Preview_PaperSail_marks"):
    bpy.ops.wm.stl_import(filepath=_ink)
    mk = bpy.context.selected_objects[0]; mk.name = mk.data.name = "Preview_PaperSail_marks"
    for v in mk.data.vertices:
        v.co.y *= 0.55
    mk.data.materials.clear(); mk.data.materials.append(bpy.data.objects["Lower_ink"].data.materials[0])
    mk["printable"] = False
    for uc in list(mk.users_collection):
        uc.objects.unlink(mk)
    sc.collection.objects.link(mk)
prev = bpy.data.collections.new("Preview - thread rig and paper sails (not printed)")
sc.collection.children.link(prev)
for ob in list(sc.collection.objects):
    if ob.name.startswith("Preview_"):
        sc.collection.objects.unlink(ob); prev.objects.link(ob)
old = bpy.data.collections.get("Collection")
if old and not old.objects:
    bpy.data.collections.remove(old)
for n in ("Margaret presentation camera",):
    if n in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)

sc.unit_settings.system = "METRIC"
sc.unit_settings.scale_length = 0.001
sc.unit_settings.length_unit = "MILLIMETERS"

sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = 1600, 1200
sc.render.film_transparent = True
w = sc.world or bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.62, 0.7, 0.78, 1); bg.inputs[1].default_value = 0.9
for n, rot, e in (("KeySun", (0.75, 0.2, 0.9), 3.5), ("FillSun", (1.1, -0.3, -2.2), 1.2)):
    if n not in bpy.data.objects:
        d = bpy.data.lights.new(n, "SUN"); d.energy = e
        o = bpy.data.objects.new(n, d); sc.collection.objects.link(o); o.rotation_euler = rot

camcol = bpy.data.collections.new("Cameras"); sc.collection.children.link(camcol)


def cam(name, eye, target, scale):
    d = bpy.data.cameras.new(name); d.type = "ORTHO"; d.ortho_scale = scale
    d.clip_start = 0.1; d.clip_end = 5000
    o = bpy.data.objects.new(name, d); camcol.objects.link(o)
    o.location = Vector(eye)
    o.rotation_euler = (Vector(target)-Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    return o


VIEWS = [("view-1", "Starboard bow quarter", (300, -330, 160), (0, 0, 82), 345, (1200, 1500)),
         ("view-2", "Port profile", (0, 600, 60), (0, 0, 95), 322, (1200, 1500)),
         ("view-3", "Starboard profile", (0, -600, 60), (0, 0, 95), 322, (1200, 1500)),
         ("view-4", "Cockpit, twin helms and teak", (-260, -170, 170), (-57, 0, 14), 100, (1600, 1200)),
         ("view-5", "Deck plan", (0, 0, 600), (0, 0, 0), 215, (1600, 1200)),
         ("view-6", "Detachable ballast bulb", (58, -200, 62), (-13, 0, -54), 88, (1600, 1200))]
cams = {v[0]: cam("Cam %s - %s" % (v[0][-1], v[1]), *v[2:5]) for v in VIEWS}
RES = {v[0]: v[5] for v in VIEWS}
sc.camera = cams["view-1"]
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(DELIVER, "Margaret.blend"), compress=True)

for key, *_ in VIEWS[:5]:
    sc.camera = cams[key]
    sc.render.resolution_x, sc.render.resolution_y = RES[key]
    sc.render.filepath = os.path.join(WORK, key + ".png")
    bpy.ops.render.render(write_still=True)

# Exploded bulb: drop the cup, show an illustrative level fill of 3 mm lead.
prev.hide_render = True
cup = bpy.data.objects["Ballast_cup"]
dg = bpy.context.evaluated_depsgraph_get()
me = cup.evaluated_get(dg).to_mesh()
verts = [cup.matrix_world @ v.co for v in me.vertices]
bvh = BVHTree.FromPolygons(verts, [list(p.vertices) for p in me.polygons])
cup.evaluated_get(dg).to_mesh_clear()
fill_top = STAB["lead_fill_top_z"]
want = STAB["lead_balls_3mm"]
r = 1.5
split = ST["bulb"]["split_z"]


def inside(p):
    h1 = bvh.ray_cast(p, Vector((0, 1, 0))); h2 = bvh.ray_cast(p, Vector((0, -1, 0)))
    h3 = bvh.ray_cast(p, Vector((0, 0, -1)))
    if not (h1[0] and h2[0] and h3[0]):
        return False
    if h1[1].y >= 0 or h2[1].y <= 0 or h3[1].z <= 0:
        return False
    return bvh.find_nearest(p)[3] >= r+0.05


cx0, cx1 = ST["bulb"]["cavity_x"]
cands = []
for iz in range(int((split-r-ST["bulb"]["floor_z"]-r)/0.25)+1):
    z = ST["bulb"]["floor_z"]+r+0.05+iz*0.25
    for ix in range(int((cx1-cx0)/0.5)+1):
        for iy in range(-16, 17):
            cands.append(Vector((cx0+ix*0.5, iy*0.5, z)))
centres = []
TILT = math.radians(float(os.environ.get("POUR_TILT", "0")))
cands.sort(key=lambda p: p.z*math.cos(TILT)+p.x*math.sin(TILT))
for p in cands:
    if all((p-q).length >= 3.0 for q in centres) and inside(p):
        centres.append(p)
discrete = len(centres)
below_fill = sum(1 for c in centres if c.z <= fill_top-0.5)
centres = centres[:want]
lead_mat = bpy.data.materials.new("Lead (illustration)")
lead_mat.diffuse_color = (0.42, 0.44, 0.47, 1)
lead_mat.use_nodes = True
bsdf = lead_mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.42, 0.44, 0.47, 1); bsdf.inputs["Metallic"].default_value = 0.8
bsdf.inputs["Roughness"].default_value = 0.45
DZ = -17.0
bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=r)
ball = bpy.context.active_object; ball.data.materials.append(lead_mat)
for i, c in enumerate(centres):
    o = ball if i == 0 else bpy.data.objects.new("Lead%03d" % i, ball.data)
    if i:
        sc.collection.objects.link(o)
    o.location = c+Vector((0, 0, DZ))
cup.location.z += DZ
for n in ("Mast", "Boom"):
    bpy.data.objects[n].hide_render = True
sc.camera = cams["view-6"]
sc.render.resolution_x, sc.render.resolution_y = RES["view-6"]
sc.render.filepath = os.path.join(WORK, "view-6.png")
bpy.ops.render.render(write_still=True)
json.dump({"illustrated_balls": len(centres), "discrete_capacity_balls_below_split": discrete, "greedy_balls_centre_below_fill_top": below_fill, "highest_illustrated_ball_top_z": round(max(c.z for c in centres)+r, 2), "drop_mm": DZ}, open(os.path.join(WORK, "exploded.json"), "w"))
print("PRESENT DONE balls", len(centres), "discrete capacity", discrete)
