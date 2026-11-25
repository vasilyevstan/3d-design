"""Margaret v7 ballast, trim and heel check (run inside Blender: -b --factory-startup -P stability_v6.py).

Inputs: MARGARET_OUT (v6 build dir with STLs + stats.json), optional PLA_G (sliced on-board PLA mass in g).
Writes stability.json next to the STLs.
"""
import bpy, bmesh, json, math, os
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

OUT = os.environ["MARGARET_OUT"]
ST = json.load(open(os.path.join(OUT, "stats.json")))
PARTS = [k for k in ST["parts"] if k not in ST.get("display_only_parts", [])]   # furler stays ashore
RHO_PLA, RHO_W, RHO_AIR, G0 = 1.24, 0.998, 1.2, 9.81


def load(name):
    bpy.ops.wm.stl_import(filepath=os.path.join(OUT, name + ".stl"))
    ob = bpy.context.selected_objects[0]
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.transform(ob.matrix_world)
    bpy.data.objects.remove(ob, do_unlink=True)
    return bm


def integrate(bm):
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    v, m, a = 0.0, Vector(), 0.0
    for f in bm.faces:
        p, q, r = [t.co for t in f.verts]
        dv = p.dot(q.cross(r))/6.0
        v += dv; m += (p+q+r)*(dv/4.0); a += f.calc_area()
    return v/1000.0, m/v, a


parts = {}
for n in PARTS:
    bm = load(n)
    v, c, a = integrate(bm)
    shell = min(v, a/2.0*0.84/1000.0)
    parts[n] = {"vol": v, "c": c, "print_vol": shell+0.07*max(v-shell, 0.0)}
    bm.free()
raw = sum(p["print_vol"] for p in parts.values())*RHO_PLA
PLA_G = float(os.environ.get("PLA_G", raw))
for p in parts.values():
    p["m"] = p["print_vol"]*RHO_PLA*PLA_G/raw
SLICE = os.environ.get("SLICE_MASS")            # mass.json from gcode_mass.py: same per-object split as hydro_check.py
if SLICE:
    GROUPS = {"Hull_lower": ["Lower_blue", "Lower_white", "Lower_ink"],
              "Hull_upper": ["Upper_white", "Upper_ink", "Upper_teak", "Window_ink"],
              "Mast": ["Mast", "Shrouds"], "Furler": ["Furler", "Furler_ink"],
              "Rudder": ["Rudder", "Rudder_ink"], "Wheel_Port": ["Wheel_Port", "WheelSpokes_Port"],
              "Wheel_Starboard": ["Wheel_Starboard", "WheelSpokes_Starboard"]}
    for obj, d in json.load(open(SLICE))["objects"].items():
        mem = [n for n in GROUPS.get(obj, [obj]) if n in parts]
        tot = sum(parts[n]["print_vol"] for n in mem)
        for n in mem:
            parts[n]["m"] = d["total_g"]*parts[n]["print_vol"]/tot if tot else 0.0

sail = ST["sail"]
SAILS = {k: (v["luff_mm"], v["foot_mm"]) for k, v in ST["sails"].items()}


def sail_geom(luff, foot):
    x0, z0 = sail["luff_x"], sail["tack_z"]
    area = 0.5*luff*foot/100.0
    return area, Vector((x0-foot/3.0, 0.0, z0+luff/3.0))


extras = []
area_full, ce_full = sail_geom(*SAILS["full"])
extras.append(("paper sail 80 g/m2 (full)", area_full*0.008, ce_full))
extras.append(("sail ties (printed rig, paper main)", 0.05, Vector((-15.0, 0.0, 110.0))))
extras.append(("deck seam CA/epoxy", 0.8, Vector((-5.0, 0.0, 2.5))))
extras.append(("bulb joint + shot glue", 0.4, Vector((ST["bulb"]["x_center"], 0.0, -47.0))))

env = load("_HydroEnvelope")
bmesh.ops.triangulate(env, faces=list(env.faces))


def submerged(rot_deg, dz):
    bm = env.copy()
    bm.transform(Matrix.Translation((0, 0, dz)) @ Matrix.Rotation(math.radians(rot_deg), 4, "X"))
    geom = list(bm.verts)+list(bm.edges)+list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=(0, 0, 0), plane_no=(0, 0, 1), clear_outer=True)
    bnd = [e for e in bm.edges if e.is_boundary]
    if bnd:
        bmesh.ops.holes_fill(bm, edges=bnd)
    v, c, _ = integrate(bm)
    bm.free()
    return v, c


disp0, cb0 = submerged(0.0, 0.0)
DISP_G = disp0*RHO_W
pla = sum(p["m"] for p in parts.values())
ext = sum(e[1] for e in extras)
lead = DISP_G-pla-ext
m_known = Vector()
for p in parts.values():
    m_known += p["c"]*p["m"]
for _, m, c in extras:
    m_known += c*m

b = ST["bulb"]
BULB_L, BULB_HW, BULB_HH, BULB_ZC, WALL, SPLIT = (b["length"]/ST["x_scale"], b["half_width"], b["half_height"],
                                                b["z_centre"], b["wall"], b["split_z"])
SX = ST["x_scale"]


def bulb_factor(u):
    u = min(max(u, 0.0), 1.0)
    f = 0.2969*math.sqrt(u)-0.1260*u-0.3516*u*u+0.2843*u**3-0.1036*u**4
    fm = 0.2969*math.sqrt(0.32)-0.1260*0.32-0.3516*0.32**2+0.2843*0.32**3-0.1036*0.32**4
    return max(0.02, f/fm)


def lead_fill(mass, packing=0.62):
    """Level fill of the open-topped cavity from the floor; returns fill height, centroid and capacity."""
    xa, xb = b["cavity_x"]
    xc = b["x_center"]
    vol_needed = mass/(11.34*packing)*1000.0
    posts = b["posts_x"]

    def slab(zl):
        v = mx = mz = 0.0
        n = 160
        for i in range(n):
            x = xa+(xb-xa)*(i+0.5)/n
            u = (xc+BULB_L*SX/2-x)/(BULB_L*SX)
            f = bulb_factor(u)
            a, c = BULB_HW*f-WALL, BULB_HH*f-WALL
            if a <= 0 or c <= 0:
                continue
            m = 40
            for j in range(m):
                z = BULB_ZC-c+(min(zl, SPLIT)-(BULB_ZC-c))*(j+0.5)/m
                if z > BULB_ZC+c:
                    continue
                w = 2*a*math.sqrt(max(0.0, 1-((z-BULB_ZC)/c)**2))
                if any(abs(x-px) < b["post_r"] for px in posts):
                    w = max(0.0, w-2*b["post_r"]*0.8)
                dA = w*(min(zl, SPLIT)-(BULB_ZC-c))/m*(xb-xa)/n
                v += dA; mx += dA*x; mz += dA*z
        return v, (mx/v if v else 0), (mz/v if v else 0)

    cap = slab(SPLIT)
    lo, hi = BULB_ZC-BULB_HH, SPLIT
    for _ in range(40):
        mid = 0.5*(lo+hi)
        if slab(mid)[0] < vol_needed:
            lo = mid
        else:
            hi = mid
    v, cx, cz = slab(hi)
    return {"fill_top_z": hi, "level_centroid": (cx, cz), "capacity_g": cap[0]/1000*11.34*packing,
            "cavity_x": (xa, xb)}


BALL_G = float(os.environ.get("LEAD_BALL_G", "0.16"))
BALL_R = float(os.environ.get("LEAD_BALL_D", "3.0"))/2


def discrete_balls():
    """Settle 3 mm spheres lowest-first into the open cup (greedy deposition on a 0.5 x 0.5 x 0.25 mm lattice).

    Every ball must sit fully below the glue plane and clear the cup and its posts by 0.05 mm.
    """
    cb = load("Ballast_cup")
    bmesh.ops.triangulate(cb, faces=list(cb.faces))
    verts = [v.co.copy() for v in cb.verts]
    polys = [[v.index for v in f.verts] for f in cb.faces]
    cb.free()
    tree = BVHTree.FromPolygons(verts, polys)
    r = BALL_R
    xa, xb = b["cavity_x"]

    def inside(p):
        h1 = tree.ray_cast(p, Vector((0, 1, 0))); h2 = tree.ray_cast(p, Vector((0, -1, 0)))
        h3 = tree.ray_cast(p, Vector((0, 0, -1)))
        if not (h1[0] and h2[0] and h3[0]) or h1[1].y >= 0 or h2[1].y <= 0 or h3[1].z <= 0:
            return False
        return tree.find_nearest(p)[3] >= r+0.05

    out, grid = [], {}
    z = b["floor_z"]+r+0.05
    while z+r <= SPLIT+1e-6:
        for ix in range(int((xb-xa)/0.5)+1):
            for iy in range(-24, 25):
                p = Vector((xa+ix*0.5, iy*0.5, z))
                k = (int(p.x//3), int(p.y//3), int(p.z//3))
                if any((p-q).length < 2*r-1e-9 for i in (-1, 0, 1) for j in (-1, 0, 1) for l in (-1, 0, 1)
                       for q in grid.get((k[0]+i, k[1]+j, k[2]+l), ())):
                    continue
                if inside(p):
                    out.append(p); grid.setdefault(k, []).append(p)
        z += 0.25
    return out


BALLS = discrete_balls()
n_need = int(math.ceil(lead/BALL_G))
used = BALLS[:n_need]
cont = lead_fill(lead)
if len(BALLS) >= n_need:
    lc = sum(used, Vector())/len(used)
    fill = {"fill_top_z": max(p.z for p in used)+BALL_R, "level_centroid": (lc.x, lc.z),
            "capacity_g": len(BALLS)*BALL_G, "cavity_x": cont["cavity_x"]}
else:
    fill = dict(cont, capacity_g=len(BALLS)*BALL_G)
# Lead x needed so the loaded LCG sits over the upright LCB (zero trim).
x_lead_need = (cb0.x*DISP_G-m_known.x)/lead
G = (m_known+Vector((x_lead_need, 0.0, fill["level_centroid"][1]))*lead)/DISP_G

# Lateral-plane centroid (CLR proxy) of the upright immersed body, by ray-casting the XZ silhouette.
bm = env.copy()
bmesh.ops.bisect_plane(bm, geom=list(bm.verts)+list(bm.edges)+list(bm.faces), dist=1e-6,
                       plane_co=(0, 0, 0), plane_no=(0, 0, 1), clear_outer=True)
bvh = BVHTree.FromBMesh(bm)
cells = sx = sz = 0.0
step = 0.5
for i in range(int(220/step)):
    x = -110+(i+0.5)*step
    for k in range(int(70/step)):
        z = -70+(k+0.5)*step
        if z > 0:
            continue
        hit = bvh.ray_cast(Vector((x, -80, z)), Vector((0, 1, 0)), 200)
        if hit[0] is not None:
            cells += 1; sx += x; sz += z
bm.free()
LAT_AREA = cells*step*step/100.0
CLR = (sx/cells, sz/cells)

heel = []
for phi in (0, 5, 10, 15, 20, 25, 30, 35, 40):
    lo, hi = -25.0, 25.0
    for _ in range(26):
        mid = 0.5*(lo+hi)
        v, c = submerged(phi, mid)
        if v*RHO_W > DISP_G:      # dz lifts the hull: too much volume -> lift more (v6 had this inverted)
            lo = mid
        else:
            hi = mid
    v, c = submerged(phi, hi)
    g = Matrix.Rotation(math.radians(phi), 4, "X") @ G
    gz = g.y-c.y
    heel.append({"phi": phi, "GZ_mm": gz, "RM_mNm": DISP_G/1000*G0*gz})


def rm_at(phi):
    for a, b_ in zip(heel, heel[1:]):
        if a["phi"] <= phi <= b_["phi"]:
            t = (phi-a["phi"])/(b_["phi"]-a["phi"])
            return a["RM_mNm"]+(b_["RM_mNm"]-a["RM_mNm"])*t
    return heel[-1]["RM_mNm"]


sails = {}
for name, (luff, foot) in SAILS.items():
    area, ce = sail_geom(luff, foot)
    arm = (ce.z-CLR[1])/1000.0
    out = {"area_cm2": round(area, 1), "luff_mm": luff, "foot_mm": foot, "CE_z": round(ce.z, 1),
           "CE_x": round(ce.x, 1), "lead_mm_CE_ahead_of_CLR": round(ce.x-CLR[0], 1)}
    for wind in (1.0, 1.5, 2.0, 3.0):
        eq = None
        for p10 in range(0, 401):
            phi = p10/10.0
            hm = 0.5*RHO_AIR*wind**2*area/1e4*1.2*arm*math.cos(math.radians(phi))**2*1000
            if rm_at(phi) >= hm:
                eq = phi
                break
        out["heel_deg_at_%.1f_mps" % wind] = eq
    sails[name] = out

res = {"PLA_g": round(pla, 2), "PLA_source": "sliced per object" if SLICE else ("sliced total" if "PLA_G" in os.environ else "volume estimate"),
       "extras_g": {e[0]: round(e[1], 2) for e in extras}, "displacement_g_at_DWL": round(DISP_G, 2),
       "LCB_x": round(cb0.x, 2), "VCB_z": round(cb0.z, 2),
       "lead_needed_g": round(lead, 2), "lead_balls_3mm": n_need,
       "lead_capacity_balls_discrete": len(BALLS), "lead_capacity_g_discrete": round(fill["capacity_g"], 1),
       "lead_capacity_g_continuum_62pct": round(cont["capacity_g"], 1), "ball_g": BALL_G, "ball_d_mm": 2*BALL_R,
       "lead_fill_top_z": round(fill["fill_top_z"], 2), "fill_method": "discrete lowest-first" if len(BALLS) >= n_need else "continuum (discrete capacity short!)",
       "lead_x_needed_for_level_trim": round(x_lead_need, 2), "cavity_x": [round(v, 2) for v in fill["cavity_x"]],
       "lead_level_centroid": [round(v, 2) for v in fill["level_centroid"]],
       "G": [round(v, 2) for v in G], "lateral_area_cm2": round(LAT_AREA, 1), "CLR_xz": [round(v, 1) for v in CLR],
       "heel": [{k: round(v, 3) for k, v in h.items()} for h in heel], "sails": sails,
       "part_mass_g": {n: round(p["m"], 2) for n, p in parts.items()}}
json.dump(res, open(os.path.join(OUT, "stability.json"), "w"), indent=1)
print("STABILITY", json.dumps(res, indent=1))
