"""Neck strength: slice Stand.stl on horizontal (print-layer) planes; section area, centroid, I about the
centroidal y axis; normal stress on each layer plane from the boat's weight acting at G.x; head deflection."""
import os, json, math, struct
import numpy as np
SD = os.environ["STAND_DIR"]; OUT = os.environ["MARGARET_OUT"]
raw = open(os.path.join(SD, "Stand.stl"), "rb").read(); n = struct.unpack("<I", raw[80:84])[0]
T = np.frombuffer(raw[84:84+50*n], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))["v"].reshape(n, 3, 3).astype(float)
st = json.load(open(os.path.join(SD, "stand.json")))
ZB = st["base"]["top_z"]; ZHB = st["fork"]["head_bottom_z"]
nrm = np.cross(T[:, 1]-T[:, 0], T[:, 2]-T[:, 0])
def section(z, xmax=-20.0):
    A = Sx = Ixx = Iyy = 0.0; xs = []
    for t, nn in zip(T, nrm):
        d = t[:, 2]-z
        if d.max() <= 0 or d.min() >= 0: continue
        pts = []
        for i in range(3):
            a, b = t[i], t[(i+1) % 3]
            if (a[2]-z)*(b[2]-z) < 0:
                s = (z-a[2])/(b[2]-a[2]); pts.append(a+s*(b-a))
        if len(pts) != 2: continue
        p, q = pts[0][:2], pts[1][:2]
        if max(p[0], q[0]) > xmax: continue
        tdir = np.array((-nn[1], nn[0]))
        if np.dot(q-p, tdir) < 0: p, q = q, p
        (x1, y1), (x2, y2) = p, q; c = x1*y2-x2*y1
        A += c/2; Sx += (x1+x2)*c/6; Iyy += (x1*x1+x1*x2+x2*x2)*c/12; Ixx += (y1*y1+y1*y2+y2*y2)*c/12
        xs += [x1, x2]
    xc = Sx/A
    return A, xc, Iyy-A*xc*xc, Ixx, min(xs), max(xs)
hj = json.load(open(os.path.join(OUT, "hydro_check.json")))
dsj = os.environ.get("DISPLAY_SAIL_JSON")
cases = {"full lead, paper sail": (hj["mass_g"]["total"], hj["G"][0])}
if dsj and os.path.exists(dsj):
    dj = json.load(open(dsj)); dm = dj["mass_g"]-dj["replaces_paper_g"]; M = hj["mass_g"]["total"]
    cases["full lead, display sail"] = (M+dm, (hj["G"][0]*M+dj["centroid"][0]*dm)/(M+dm))
E = 2300.0           # MPa, FDM PLA across layers (conservative)
S_Z = 15.0           # MPa, PLA interlayer tensile strength, conservative (published 15-35)
rows = []
zs = np.arange(ZB+0.05, ZHB-0.05, 0.25)
secs = [section(z) for z in zs]
res = {"E_MPa": E, "interlayer_strength_MPa": S_Z, "cases": {}}
for name, (mg, gx) in cases.items():
    W = mg/1000*9.81
    worst = (0, None); th = dl = 0.0
    for k, (z, (A, xc, I, Ix, x0, x1)) in enumerate(zip(zs, secs)):
        M = W*(gx-xc)                                    # N mm, load ahead of the section -> tension at the rear face
        sig_t = M*(xc-x0)/I-W/A                         # rear face (tension under a forward load)
        sig_c = -M*(x1-xc)/I-W/A
        if sig_t > worst[0]: worst = (sig_t, round(float(z), 2), round(A, 2), round(x1-x0, 2))
        if k:
            dz = zs[k]-zs[k-1]; lean = math.atan2(xc-secs[k-1][1], dz); ds = dz/math.cos(lean)
            Ip = I*math.cos(lean)**3                     # section square to the neck axis
            th += M/(E*Ip)*ds; dl += M*(gx-xc)/(E*Ip)*ds
    res["cases"][name] = {"boat_g": round(mg, 2), "G_x": round(gx, 2), "W_N": round(W, 4),
        "max_layer_tension_MPa": round(worst[0], 3), "at_z": worst[1], "section_area_mm2": worst[2], "section_depth_x_mm": worst[3],
        "safety_factor_static": round(S_Z/worst[0], 1), "safety_factor_3g_bump": round(S_Z/(3*worst[0]), 1),
        "head_rotation_deg": round(math.degrees(th), 3), "load_point_sag_mm": round(dl, 3),
        "sag_after_creep_x2_mm": round(2*dl, 3)}
res["sections"] = [{"z": round(float(z), 2), "A": round(s[0], 2), "xc": round(s[1], 2), "Iyy": round(s[2], 1), "depth": round(s[5]-s[4], 2)}
                   for z, s in list(zip(zs, secs))[::8]]
json.dump(res, open(os.environ.get("CALC_OUT", os.path.join(SD, "stand_strength.json")), "w"), indent=1)
print(json.dumps(res["cases"], indent=1)); print(json.dumps(res["sections"]))
