"""Lay Margaret v7 out on the Bambu P2S plates (run in Blender -b --factory-startup -P plate_v7.py).

Reads the assembled per-colour STLs from MARGARET_OUT, applies print orientations, places every
component on its 256 x 256 plate and writes per-colour STLs that keep their relative offsets
(plate.json uses assemble_index so Bambu Studio merges colours into one object and does not re-arrange).
Rev 17: one project, four plates (1 upper hull; 2 lower hull + keel + rudder; 3 spars + wheels; 4 display stand +
display sail), support blockers over both mast-bore halves (the slicer otherwise fills the blind socket with a support
column that stops the mast 5.8 mm high), and objects.json for patch3mf.py (real names, object filament, per-object
settings).
"""
import bpy, bmesh, json, math, os, struct
from mathutils import Matrix, Vector

OUT = os.environ["MARGARET_OUT"]
PLATE = os.path.join(OUT, "plate"); os.makedirs(PLATE, exist_ok=True)
BED = 256.0
WHITE, BLUE, INK, TEAK = 1, 2, 3, 4
R = lambda deg, ax: Matrix.Rotation(math.radians(deg), 4, ax)
# component: ([(part, filament)], print orientation, plate centre (x, y)); "bed" = STL already in print orientation
PLATES = [("Margaret 1 - upper hull", ["Hull_upper"]),
          ("Margaret 2 - lower hull, keel, rudder", ["Hull_lower", "Fin_cap", "Ballast_cup", "Rudder"]),
          ("Margaret 3 - mast, furler, boom, wheels", ["Mast", "Furler", "Boom", "Wheel_Port", "Wheel_Starboard"]),
          ("Margaret 4 - display stand and display sail", ["Stand", "Display_sail"])]
MAIN = {"Hull_upper": WHITE, "Hull_lower": BLUE, "Fin_cap": BLUE, "Ballast_cup": BLUE, "Rudder": BLUE, "Mast": WHITE,
        "Furler": WHITE, "Boom": WHITE, "Wheel_Port": INK, "Wheel_Starboard": INK, "Stand": INK, "Display_sail": WHITE}
SETTINGS = {"Stand": {"enable_support": "1", "support_type": "tree(auto)", "support_on_build_plate_only": "0",
                      "wall_loops": "3", "sparse_infill_density": "15%"},
            "Display_sail": {"enable_support": "0", "wall_loops": "3", "sparse_infill_density": "15%"}}
COMPONENTS = {
    "Hull_lower": ([("Lower_blue", BLUE), ("Lower_white", WHITE), ("Lower_ink", INK)], R(180, "X"), (107.0, 30.9)),
    "Hull_upper": ([("Upper_white", WHITE), ("Upper_ink", INK), ("Window_ink", INK), ("Upper_teak", TEAK)],
                   Matrix.Identity(4), (107.0, 92.8)),
    # rev 12: the rev 11 printed railings were removed
    # display furler (stays ashore when sailing): flat face y=-0.6 down, turned along the free band
    "Furler": ([("Furler", WHITE), ("Furler_ink", INK)], ("scanZ", R(90, "X"), 95.0, 118.0), (128.0, 150.0)),  # rev16: thicker furler, re-centred in the free band
    "Fin_cap": ([("Fin_cap", BLUE)], Matrix.Identity(4), (31.0, 171.4)),
    "Ballast_cup": ([("Ballast_cup", BLUE)], Matrix.Identity(4), (95.0, 172.3)),
    "Rudder": ([("Rudder", BLUE), ("Rudder_ink", INK)], R(90, "Z") @ R(90, "X"), (163.0, 170.3)),
    "Wheel_Port": ([("Wheel_Port", INK), ("WheelSpokes_Port", WHITE)], R(-90, "Y"), (194.0, 171.1)),
    "Wheel_Starboard": ([("Wheel_Starboard", INK), ("WheelSpokes_Starboard", WHITE)], R(-90, "Y"), (212.0, 171.1)),
    "Boom": ([("Boom", WHITE)], Matrix.Identity(4), (40.0, 184.1)),
    # mast prints on its flat aft face; the navy shroud frame (now spread to the outboard chainplates) lies on the
    # bed in that same plane along the top edge
    "Mast": ([("Mast", WHITE), ("Shrouds", INK)], R(-90, "Y"), (128.0, 227.0)),
    # plate 4: the stand and display sail come already in print orientation from stand_neck.py / display_sail.py
    "Stand": ([("stand/Stand-bed", INK)], "bed", (152.0, 150.0)),
    "Display_sail": ([("dsail/Display_sail-bed", WHITE), ("dsail/Display_sail_ink-bed", INK)], "bed", (50.0, 128.0)),
}
COMPONENTS.update(json.loads(os.environ.get("PLATE_OVERRIDE", "{}")))
SEAM = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hull_params_v7.json")))["seam"]


def heel_box():
    """Mast heel footprint (assembled export coordinates) below the deck, from Mast.stl."""
    pts = [p for t in tris_of("Mast") for p in t if p.z < 0.0]
    return [min(p.x for p in pts), max(p.x for p in pts), min(p.y for p in pts), max(p.y for p in pts)]


def box_tris(x0, x1, y0, y1, z0, z1):
    v = [Vector((x, y, z)) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    q = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    return [(v[a], v[b], v[c]) for a, b, c, d in q] + [(v[a], v[c], v[d]) for a, b, c, d in q]


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


def scan_z(tris, base, a0, a1):
    """Turn about Z (after base) to the angle with the smallest y-extent: long display parts lie along x."""
    pts = [base @ p for t in tris for p in t]
    best = None
    for k in range(int((a1-a0)*4)+1):
        a = a0+k*0.25
        m = R(a, "Z")
        ys = [(m @ p).y for p in pts]
        if best is None or max(ys)-min(ys) < best[0]:
            best = (max(ys)-min(ys), a)
    print("SCANZ angle", best[1], "y extent", round(best[0], 2))
    return R(best[1], "Z") @ base


hx0, hx1, hy0, hy1 = heel_box()
# support blockers over the mast bore (assembled coordinates): the blind lower socket (z SEAM-5.8 .. SEAM) through its
# overhanging floor, from below the bed; the upper through-bore from below the bed up past where it opens
BLOCKERS = {"Hull_lower": [(hx0-0.9, hx1+0.9, hy0-0.9, hy1+0.9, SEAM-7.0, SEAM+1.0)],
            "Hull_upper": [(hx0-0.9, hx1+0.9, hy0-0.9, hy1+0.9, SEAM-1.0, SEAM+27.0)]}
plates, layout, objects, idx = [], {}, {}, 0
for pname, comps in PLATES:
  recipe = []
  for comp in comps:
    members, rot, centre = COMPONENTS[comp]
    idx += 1
    objects[str(idx)] = {"name": comp, "extruder": MAIN[comp], "settings": SETTINGS.get(comp, {})}
    data = {}
    raw = [(fil, tris_of(part)) for part, fil in members]
    if rot == "bed":
        rot = Matrix.Identity(4)
    if isinstance(rot, tuple):
        rot = scan_z([t for _, ts in raw for t in ts], *rot[1:])
    for fil, ts in raw:
        data.setdefault(fil, []).extend(tuple(rot @ p for p in t) for t in ts)
    pts = [p for ts in data.values() for t in ts for p in t]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    off = Vector((centre[0]-(lo.x+hi.x)/2, centre[1]-(lo.y+hi.y)/2, -lo.z))
    box = [lo.x+off.x, lo.y+off.y, hi.x+off.x, hi.y+off.y, hi.z-lo.z]
    if box[0] < 2 or box[1] < 2 or box[2] > BED-2 or box[3] > BED-2:
        raise RuntimeError("%s off the bed: %s" % (comp, [round(v, 1) for v in box]))
    layout[comp] = {"plate": len(plates)+1, "box": [round(v, 2) for v in box], "rotation": [list(r) for r in rot],
                    "offset": list(off)}
    if box[2] > 212.0 and box[1] < 64.0:
        raise RuntimeError("%s on the prime tower: %s" % (comp, [round(v, 1) for v in box]))
    vols = sorted(data.items())
    for k, b in enumerate(BLOCKERS.get(comp, [])):
        vols.append(("blk%d" % k, [tuple(rot @ p for p in t) for t in box_tris(*b)]))
    for fil, ts in vols:
        path = os.path.join(PLATE, "%s-%s.stl" % (comp, fil))
        with open(path, "wb") as f:
            f.write(bytes(80)+struct.pack("<I", len(ts)))
            for t in ts:
                a, b, c = [p+off for p in t]
                n = (b-a).cross(c-a)
                n = n.normalized() if n.length > 0 else n
                f.write(struct.pack("<12fH", *n, *a, *b, *c, 0))
        if isinstance(fil, str):
            zs = [p.z+off.z for t in ts for p in t]
            print("BLOCKER", comp, "bed z %.2f .. %.2f" % (min(zs), max(zs)))
            recipe.append({"path": path, "count": 1, "filaments": [1], "assemble_index": [idx],
                           "subtype": "support_blocker"})
        else:
            recipe.append({"path": path, "count": 1, "filaments": [fil], "assemble_index": [idx]})
    print("PLACED", len(plates)+1, comp, [round(v, 1) for v in box])
  plates.append({"plate_name": pname, "need_arrange": False, "objects": recipe})

for i, (a, ba) in enumerate(layout.items()):
    for b, bb in list(layout.items())[i+1:]:
        if ba["plate"] == bb["plate"] and ba["box"][0] < bb["box"][2]+1.5 and bb["box"][0] < ba["box"][2]+1.5 and \
           ba["box"][1] < bb["box"][3]+1.5 and bb["box"][1] < ba["box"][3]+1.5:
            raise RuntimeError("overlap %s / %s" % (a, b))
json.dump({"plates": plates}, open(os.path.join(PLATE, "plate.json"), "w"), indent=1)
json.dump(objects, open(os.path.join(PLATE, "objects.json"), "w"), indent=1)
json.dump(layout, open(os.path.join(PLATE, "layout.json"), "w"), indent=1)
print("PLATE OK", len(plates), "plates", sum(len(p["objects"]) for p in plates), "volumes")
