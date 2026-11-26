"""Independent float / trim / stability check for Margaret (numpy only, no Blender).

Reads the exported STLs of a build directory and answers: what does the loaded boat weigh, where is its centre of
gravity, where does it float (sinkage + trim), and how much righting arm does it have from 0 to 180 degrees of heel.

Method (deliberately different from the Blender script stability_v6.py):
  * submerged volume = signed-tetrahedron sum over the triangles of the closed hull envelope clipped to z <= 0, with the
    reference point on the water plane (the lid of the clipped solid then contributes exactly zero volume and moment);
  * free trim at every heel angle: sinkage and pitch are solved together (secant iterations) so that buoyancy = weight
    and the centre of buoyancy is vertically in line with G in the fore-aft direction;
  * lead centroid from a level pour into a voxelised copy of the ballast cup cavity (lowest cells first).

env: MARGARET_OUT (build dir), PLA_G (sliced on-board PLA grams), LEAD_BALLS (optional fixed ball count),
     LEAD_BALL_G (0.16), PACKING (0.60), HYDRO_JSON (output path, default <OUT>/hydro_check.json)
"""
import json, math, os, struct, sys
import numpy as np

OUT = os.environ["MARGARET_OUT"]
ST = json.load(open(os.path.join(OUT, "stats.json")))
RHO_W, RHO_PLA, RHO_PB = 0.998, 1.24, 11.34          # g/cm3 (fresh water, PLA, lead)
BALL_G = float(os.environ.get("LEAD_BALL_G", "0.16"))
PACK = float(os.environ.get("PACKING", "0.60"))


def read_stl(path):
    data = open(path, "rb").read()
    n = struct.unpack("<I", data[80:84])[0]
    if 84+50*n == len(data):
        rec = np.frombuffer(data, dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]), count=n, offset=84)
        return rec["v"].astype(np.float64)
    pts = [list(map(float, l.split()[1:4])) for l in data.decode().splitlines() if l.strip().startswith("vertex")]
    return np.array(pts, dtype=np.float64).reshape(-1, 3, 3)


def closed_check(T):
    v = T.reshape(-1, 3).round(5)
    _, idx = np.unique(v, axis=0, return_inverse=True)
    f = idx.reshape(-1, 3)
    e = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1)
    _, cnt = np.unique(e, axis=0, return_counts=True)
    return int((cnt != 2).sum())


def vol_centroid(T):
    p, q, r = T[:, 0], T[:, 1], T[:, 2]
    dv = np.einsum("ij,ij->i", p, np.cross(q, r))/6.0
    V = dv.sum()
    C = (dv[:, None]*(p+q+r)/4.0).sum(0)/V
    A = 0.5*np.linalg.norm(np.cross(q-p, r-p), axis=1).sum()
    return V/1000.0, C, A


def clip_below(T):
    """Triangles of T clipped to z <= 0, orientation preserved."""
    z = T[:, :, 2]
    below = z <= 0.0
    nb = below.sum(1)
    out = [T[nb == 3]]
    for k in (1, 2):
        S = T[nb == k]
        if not len(S):
            continue
        bz = S[:, :, 2] <= 0.0
        odd = np.argmax(bz if k == 1 else ~bz, axis=1)       # index of the vertex alone on its side
        R = np.stack([np.roll(S[i], -odd[i], axis=0) for i in range(len(S))]) if len(S) < 64 else \
            S[np.arange(len(S))[:, None], (odd[:, None]+np.arange(3)[None, :]) % 3]
        o, a, b = R[:, 0], R[:, 1], R[:, 2]

        def cut(p, q):
            t = (p[:, 2]/(p[:, 2]-q[:, 2]))[:, None]
            return p+(q-p)*t
        if k == 1:
            out.append(np.stack([o, cut(o, a), cut(o, b)], 1))
        else:
            ia, ib = cut(o, a), cut(b, o)
            out.append(np.stack([ia, a, b], 1)); out.append(np.stack([ia, b, ib], 1))
    return np.concatenate(out)


def rot(phi, theta):
    """Heel phi about x (port side up = starboard down for phi > 0), then pitch theta about y (bow down for theta > 0)."""
    c, s = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    Rx = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    c, s = math.cos(math.radians(theta)), math.sin(math.radians(theta))
    Ry = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return Ry @ Rx


ENV = read_stl(os.path.join(OUT, "_HydroEnvelope.stl"))
ENV_OPEN_EDGES = closed_check(ENV)
ENV_V, ENV_C, _ = vol_centroid(ENV)


def float_state(phi, theta, dz):
    R = rot(phi, theta)
    W = ENV @ R.T
    W[:, :, 2] += dz
    S = clip_below(W)
    if not len(S):
        return 0.0, np.zeros(3)
    v, c, _ = vol_centroid(S)
    return v, c


def secant(f, x0, x1, tol=1e-7, it=60):
    f0, f1 = f(x0), f(x1)
    for _ in range(it):
        if abs(f1) < tol or f1 == f0:
            break
        x0, x1, f0 = x1, x1-f1*(x1-x0)/(f1-f0), f1
        f1 = f(x1)
    return x1


def equilibrium(phi, mass_g, Gb, theta0=0.0):
    """Solve sinkage dz and pitch theta at heel phi. Returns dict with GZ etc."""
    target = mass_g/RHO_W/1.0    # cm3

    def sink(theta):
        return secant(lambda dz: float_state(phi, theta, dz)[0]-target, 0.0, 1.0, 1e-6)

    def moment(theta):
        dz = sink(theta)
        _, c = float_state(phi, theta, dz)
        g = rot(phi, theta) @ Gb
        return c[0]-g[0]
    theta = secant(moment, theta0, theta0+0.2, 1e-5)
    dz = sink(theta)
    v, c = float_state(phi, theta, dz)
    g = rot(phi, theta) @ Gb+np.array([0, 0, dz])
    return {"phi": phi, "theta": theta, "dz": dz, "vol": v, "B": c, "G": g, "GZ": g[1]-c[1]}


# ------------------------------------------------------------------ masses
parts = {}
for n in [k for k in ST["parts"] if k not in ST.get("display_only_parts", [])]:   # furler stays ashore
    T = read_stl(os.path.join(OUT, n+".stl"))
    v, c, a = vol_centroid(T)
    shell = min(v, a/2.0*0.84/1000.0)                 # 2 perimeters of 0.42 mm, both faces counted once
    parts[n] = {"vol": v, "c": c, "print_vol": shell+0.15*max(v-shell, 0.0)}
raw = sum(p["print_vol"] for p in parts.values())*RHO_PLA
PLA_G = float(os.environ.get("PLA_G", raw))
for p in parts.values():
    p["m"] = p["print_vol"]*RHO_PLA*PLA_G/raw
SLICE = os.environ.get("SLICE_MASS")            # mass.json from gcode_mass.py: distribute sliced grams per printed object
if SLICE:
    GROUPS = {"Hull_lower": ["Lower_blue", "Lower_white", "Lower_ink"],
              "Hull_upper": ["Upper_white", "Upper_ink", "Upper_teak", "Window_ink"],
              "Mast": ["Mast", "Shrouds"], "Furler": ["Furler", "Furler_ink"],
              "Rails": ["Rail_Port", "Rail_Starboard", "RailAft_Port", "RailAft_Starboard"],
              "Rudder": ["Rudder", "Rudder_ink"], "Wheel_Port": ["Wheel_Port", "WheelSpokes_Port"],
              "Wheel_Starboard": ["Wheel_Starboard", "WheelSpokes_Starboard"]}
    for obj, d in json.load(open(SLICE))["objects"].items():
        mem = [n for n in GROUPS.get(obj, [obj]) if n in parts]
        tot = sum(parts[n]["print_vol"] for n in mem)
        for n in mem:
            parts[n]["m"] = d["total_g"]*parts[n]["print_vol"]/tot if tot else 0.0

sail = ST["sail"]; b = ST["bulb"]; rig = ST["rig"]
full = ST["sails"]["full"]
EXTRAS = [("paper sail 80 g/m2 (full)", full["area_cm2"]*0.008, np.array([sail["luff_x"]-full["foot_mm"]/3, 0, sail["tack_z"]+full["luff_mm"]/3])),
          ("sail ties (printed rig, paper main)", 0.05, np.array([-15.0, 0, 110.0])),
          ("deck seam glue", 0.8, np.array([-5.0, 0, 2.5])),
          ("bulb joint + lead glue", 0.4, np.array([b["x_center"], 0, -47.0]))]
m_pla = sum(p["m"] for p in parts.values())
M_known = m_pla+sum(e[1] for e in EXTRAS)
mom_known = sum(p["m"]*p["c"] for p in parts.values())+sum(e[1]*e[2] for e in EXTRAS)

# ------------------------------------------------------------------ cavity voxels (lead pour)
CUP = read_stl(os.path.join(OUT, "Ballast_cup.stl"))


def cavity_cells(h=0.25):
    lo, hi = CUP.reshape(-1, 3).min(0), CUP.reshape(-1, 3).max(0)
    xs = np.arange(lo[0]+h/2, hi[0], h); zs = np.arange(lo[2]+h/2, min(hi[2], b["split_z"]), h)
    ys = np.arange(lo[1]+h/2, hi[1], h)
    # y-ray parity per (x, z) column: intersections of the line (x, *, z) with every triangle
    p, q, r = CUP[:, 0], CUP[:, 1], CUP[:, 2]
    cells = []
    for x in xs:
        sel = (np.minimum(np.minimum(p[:, 0], q[:, 0]), r[:, 0]) <= x) & (np.maximum(np.maximum(p[:, 0], q[:, 0]), r[:, 0]) >= x)
        P, Q, R_ = p[sel], q[sel], r[sel]
        for z in zs:
            # barycentric in the xz projection
            d = (Q[:, 0]-P[:, 0])*(R_[:, 2]-P[:, 2])-(R_[:, 0]-P[:, 0])*(Q[:, 2]-P[:, 2])
            ok = np.abs(d) > 1e-12
            u = ((x-P[:, 0])*(R_[:, 2]-P[:, 2])-(R_[:, 0]-P[:, 0])*(z-P[:, 2]))[ok]/d[ok]
            w = ((Q[:, 0]-P[:, 0])*(z-P[:, 2])-(x-P[:, 0])*(Q[:, 2]-P[:, 2]))[ok]/d[ok]
            m = (u >= 0) & (w >= 0) & (u+w <= 1)
            yh = (P[ok][:, 1]*(1-u-w)+Q[ok][:, 1]*u+R_[ok][:, 1]*w)[m]
            yh = np.sort(yh)
            if len(yh) < 4:
                continue
            # solid intervals are [yh0,yh1], [yh2,yh3]...; cavity = gap between first and last solid interval
            inner_lo, inner_hi = yh[1], yh[-2]
            for y in ys[(ys > inner_lo) & (ys < inner_hi)]:
                k = np.searchsorted(yh, y)
                if k % 2 == 0:                       # outside solid, between walls → cavity
                    cells.append((x, y, z))
    return np.array(cells), h**3/1000.0


CELLS, DV = cavity_cells()
order = np.argsort(CELLS[:, 2], kind="stable")
CELLS = CELLS[order]
CAP_G = len(CELLS)*DV*RHO_PB*PACK


POUR_TILT = float(os.environ.get("POUR_TILT", "0"))     # cup propped nose-up by this angle while the lead sets


def tilt_order(deg):
    t = math.radians(deg)
    h = CELLS[:, 2]*math.cos(t)+CELLS[:, 0]*math.sin(t)
    return np.argsort(h, kind="stable")


def lead_centroid(mass, deg=None):
    deg = POUR_TILT if deg is None else deg
    n = int(round(mass/(RHO_PB*PACK)/DV))
    n = max(1, min(n, len(CELLS)))
    sel = CELLS[tilt_order(deg)[:n]]
    return sel.mean(0), sel[:, 2].max(), sel[:, 0].max()


# lead needed so the boat floats at the design waterline z = 0 (upright)
DISP0, _ = float_state(0.0, 0.0, 0.0)
lead_need = DISP0*RHO_W-M_known
balls = int(os.environ.get("LEAD_BALLS", math.ceil(lead_need/BALL_G)))
lead = balls*BALL_G
lc, fill_top, fill_front = lead_centroid(lead)
M = M_known+lead
G = (mom_known+lead*lc)/M

upr = equilibrium(0.0, M, G)
# lead x that would give zero trim (user can bias balls fore/aft before gluing)
x_zero_trim = (DISP0*RHO_W*float_state(0.0, 0.0, 0.0)[1][0]-mom_known[0])/lead if lead > 0 else None

pour_scan = []
for deg in (0, 10, 20, 30, 40, 50, 60, 70, 80, 90):
    c_, top_, front_ = lead_centroid(lead, deg)
    Gd = (mom_known+lead*c_)/M
    e_ = equilibrium(0.0, M, Gd)
    pour_scan.append({"tilt_deg": deg, "lead_x": round(float(c_[0]), 2), "front_x": round(float(front_), 2),
                      "top_z": round(float(top_), 2), "trim_deg_bow_down": round(e_["theta"], 3)})
curve = []
th = upr["theta"]
for phi in list(range(0, 181, 5)):
    e = equilibrium(float(phi), M, G, th)
    th = e["theta"]
    curve.append({"phi": phi, "GZ_mm": round(e["GZ"], 3), "trim_deg": round(e["theta"], 3), "sink_mm": round(e["dz"], 3)})
# heel angle at which marker points reach the water (starboard side down for phi > 0, so use y < 0)
XS = ST["x_scale"]
MARKS = {"platform aft corner (wets, harmless)": (-92.0*XS, -20.0, 4.5),
         "cockpit sill at the walk-through (water into cockpit)": (-82.5*XS, -8.0, 10.3),
         "deck edge amidships": (-15.0*XS, -31.5, 15.6)}
immersion = {}
for nm, p in MARKS.items():
    prev = None
    for c_ in curve:
        z_ = (rot(c_["phi"], c_["trim_deg"]) @ np.array(p))[2]+c_["sink_mm"]
        if z_ <= 0 and prev is not None:
            pphi, pz = prev
            immersion[nm] = round(pphi+(c_["phi"]-pphi)*pz/(pz-z_), 1)
            break
        prev = (c_["phi"], z_)
avs = None
for a_, b_ in zip(curve, curve[1:]):
    if a_["GZ_mm"] > 0 >= b_["GZ_mm"] and b_["phi"] > 0:
        avs = a_["phi"]+(b_["phi"]-a_["phi"])*a_["GZ_mm"]/(a_["GZ_mm"]-b_["GZ_mm"])
        break
gz_max = max(curve, key=lambda c: c["GZ_mm"])
gm = curve[1]["GZ_mm"]/math.sin(math.radians(5))

xs_ = ST["x_scale"]
L_half = 98.0
bow_z = upr["dz"]-math.tan(math.radians(upr["theta"]))*L_half
stern_z = upr["dz"]+math.tan(math.radians(upr["theta"]))*L_half
res = {
    "envelope": {"open_edges": ENV_OPEN_EDGES, "volume_cm3": round(ENV_V, 2)},
    "mass_g": {"pla_on_board": round(m_pla, 2), "extras": round(M_known-m_pla, 2), "lead": round(lead, 2),
               "lead_balls": balls, "total": round(M, 2),
               "parts": {k: round(v["m"], 2) for k, v in sorted(parts.items(), key=lambda kv: -kv[1]["m"])}},
    "lead_needed_for_DWL_g": round(lead_need, 2),
    "cup_capacity_g_at_packing": round(CAP_G, 2), "cup_capacity_balls": int(CAP_G/BALL_G), "packing": PACK,
    "pour_tilt_deg": POUR_TILT, "lead_fill_top_z": round(fill_top, 2), "lead_front_x": round(float(fill_front), 2),
    "lead_centroid": [round(v, 2) for v in lc], "pour_scan": pour_scan,
    "G": [round(v, 2) for v in G], "B_upright": [round(v, 2) for v in upr["B"]],
    "upright": {"sinkage_below_DWL_mm": round(-upr["dz"], 2), "trim_deg_bow_down": round(upr["theta"], 3),
                "waterline_shift_bow_mm": round(-bow_z, 2), "waterline_shift_stern_mm": round(-stern_z, 2)},
    "lead_x_for_zero_trim": round(x_zero_trim, 2) if x_zero_trim is not None else None,
    "cavity_x_range": [round(CELLS[:, 0].min(), 1), round(CELLS[:, 0].max(), 1)],
    "GM_mm_small_angle": round(gm, 2), "GZ_max": gz_max, "AVS_deg": round(avs, 1) if avs else ">180",
    "reserve_buoyancy_g": round(ENV_V*RHO_W-M, 1), "immersion_heel_deg": immersion,
    "curve": curve,
}
path = os.environ.get("HYDRO_JSON", os.path.join(OUT, "hydro_check.json"))
json.dump(res, open(path, "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "curve"}, indent=1))
print("phi  GZ_mm  trim")
for c in curve:
    print("%3d %7.2f %6.2f" % (c["phi"], c["GZ_mm"], c["trim_deg"]))
