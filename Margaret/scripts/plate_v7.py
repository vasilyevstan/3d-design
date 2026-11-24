"""Lay Margaret v7 out on one Bambu P2S plate (run in Blender -b --factory-startup -P plate_v7.py).

Reads the assembled per-colour STLs from MARGARET_OUT, applies print orientations, places every
component on the 256 x 256 bed and writes per-colour STLs that keep their relative offsets
(plate.json uses assemble_index so Bambu Studio merges colours into one object and does not re-arrange).
"""
import bpy, bmesh, json, math, os, struct
from mathutils import Matrix, Vector

OUT = os.environ["MARGARET_OUT"]
PLATE = os.path.join(OUT, "plate"); os.makedirs(PLATE, exist_ok=True)
BED = 256.0
WHITE, BLUE, INK, TEAK = 1, 2, 3, 4
R = lambda deg, ax: Matrix.Rotation(math.radians(deg), 4, ax)
# component: ([(part, filament)], print orientation, plate centre (x, y))
COMPONENTS = {
    "Hull_lower": ([("Lower_blue", BLUE), ("Lower_white", WHITE), ("Lower_ink", INK)], R(180, "X"), (109.0, 42.0)),
    "Hull_upper": ([("Upper_white", WHITE), ("Upper_ink", INK), ("Window_ink", INK), ("Upper_teak", TEAK)],
                   Matrix.Identity(4), (109.0, 113.0)),
    "Mast": ([("Mast", WHITE)], R(-90, "Y"), (128.0, 236.0)),
    "Boom": ([("Boom", WHITE)], Matrix.Identity(4), (60.0, 204.0)),
    "Fin_cap": ([("Fin_cap", BLUE)], Matrix.Identity(4), (39.0, 172.0)),
    "Ballast_cup": ([("Ballast_cup", BLUE)], Matrix.Identity(4), (109.0, 172.0)),
    "Rudder": ([("Rudder", BLUE), ("Rudder_ink", INK)], R(90, "X"), (160.0, 184.0)),
    "Wheel_Port": ([("Wheel_Port", INK), ("WheelSpokes_Port", WHITE)], R(-90, "Y"), (186.0, 178.0)),
    "Wheel_Starboard": ([("Wheel_Starboard", INK), ("WheelSpokes_Starboard", WHITE)], R(-90, "Y"), (204.0, 178.0)),
}
COMPONENTS.update(json.loads(os.environ.get("PLATE_OVERRIDE", "{}")))


def tris_of(name):
    bpy.ops.wm.stl_import(filepath=os.path.join(OUT, name+".stl"))
    ob = bpy.context.selected_objects[0]
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.transform(ob.matrix_world)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bad = sum(1 for e in bm.edges if not e.is_manifold)
    if bad:
        raise RuntimeError("%s has %d non-manifold edges" % (name, bad))
    out = [tuple(v.co.copy() for v in f.verts) for f in bm.faces]
    bm.free(); bpy.data.objects.remove(ob, do_unlink=True)
    return out


recipe, layout = [], {}
for idx, (comp, (members, rot, centre)) in enumerate(COMPONENTS.items(), 1):
    data = {}
    for part, fil in members:
        data.setdefault(fil, []).extend(tuple(rot @ p for p in t) for t in tris_of(part))
    pts = [p for ts in data.values() for t in ts for p in t]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    off = Vector((centre[0]-(lo.x+hi.x)/2, centre[1]-(lo.y+hi.y)/2, -lo.z))
    box = [lo.x+off.x, lo.y+off.y, hi.x+off.x, hi.y+off.y, hi.z-lo.z]
    if box[0] < 2 or box[1] < 2 or box[2] > BED-2 or box[3] > BED-2:
        raise RuntimeError("%s off the bed: %s" % (comp, [round(v, 1) for v in box]))
    layout[comp] = {"box": [round(v, 2) for v in box], "rotation": [list(r) for r in rot], "offset": list(off)}
    for fil, ts in sorted(data.items()):
        path = os.path.join(PLATE, "%s-%d.stl" % (comp, fil))
        with open(path, "wb") as f:
            f.write(bytes(80)+struct.pack("<I", len(ts)))
            for t in ts:
                a, b, c = [p+off for p in t]
                n = (b-a).cross(c-a)
                n = n.normalized() if n.length > 0 else n
                f.write(struct.pack("<12fH", *n, *a, *b, *c, 0))
        recipe.append({"path": path, "count": 1, "filaments": [fil], "assemble_index": [idx]})
    print("PLACED", comp, [round(v, 1) for v in box])

boxes = list(layout.items())
for i, (a, ba) in enumerate(boxes):
    for b, bb in boxes[i+1:]:
        if ba["box"][0] < bb["box"][2]+1.5 and bb["box"][0] < ba["box"][2]+1.5 and \
           ba["box"][1] < bb["box"][3]+1.5 and bb["box"][1] < ba["box"][3]+1.5:
            raise RuntimeError("overlap %s / %s" % (a, b))
json.dump({"plates": [{"plate_name": "Margaret", "need_arrange": False, "objects": recipe}]},
          open(os.path.join(PLATE, "plate.json"), "w"), indent=1)
json.dump(layout, open(os.path.join(PLATE, "layout.json"), "w"), indent=1)
print("PLATE OK", len(recipe), "volumes")
