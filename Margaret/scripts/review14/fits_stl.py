"""Nominal fit check on the exported STLs: slice each joint and measure clearance per side."""
import json, struct, sys, numpy as np
V = sys.argv[1] if len(sys.argv) > 1 else "v7j"
D = f"yacht-build/{V}"
def stl(*names):
    out = []
    for n in names:
        b = open(f"{D}/{n}.stl", "rb").read(); k = struct.unpack("<I", b[80:84])[0]
        a = np.frombuffer(b[84:84+k*50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
        out.append(a["v"].reshape(-1, 3, 3).astype(float))
    return np.concatenate(out)
def section(T, ax, c):
    """Segments of the mesh cut by plane coord[ax] = c, in the other two coords."""
    o = [i for i in range(3) if i != ax]; d = T[:, :, ax]-c
    m = (d.min(1) < 0) & (d.max(1) > 0); S = []
    for t, dd in zip(T[m], d[m]):
        p = [t[i]+(t[(i+1) % 3]-t[i])*dd[i]/(dd[i]-dd[(i+1) % 3]) for i in range(3) if (dd[i] < 0) != (dd[(i+1) % 3] < 0)]
        if len(p) == 2: S.append((p[0][o], p[1][o]))
    return np.array(S).reshape(-1, 2, 2)
def ray(S, c, u):
    """Distances from point c along unit direction u to every segment crossing (sorted)."""
    a, b = S[:, 0]-c, S[:, 1]-c; e = b-a; den = u[0]*e[:, 1]-u[1]*e[:, 0]
    with np.errstate(divide="ignore", invalid="ignore"):
        t = (a[:, 0]*e[:, 1]-a[:, 1]*e[:, 0])/den; s = (a[:, 0]*u[1]-a[:, 1]*u[0])/den
    ok = (np.abs(den) > 1e-12) & (s >= 0) & (s <= 1) & (t > 0)
    return np.sort(t[ok])
def inside(S, c):
    return len(ray(S, c, np.array([0.7071, 0.7071]))) % 2 == 1
def half_widths(S, c):
    """Distance to the first wall along +u1,-u1,+u2,-u2 from c (c in a void) or None if c is in material."""
    if inside(S, c): return None
    return [ray(S, c, np.array(u, float))[:1].tolist() or [None] for u in ((1, 0), (-1, 0), (0, 1), (0, -1))]
st = json.load(open(f"{D}/stats.json")); SX = st["x_scale"]
HULL = stl("Lower_blue", "Lower_white", "Lower_ink", "Upper_white", "Upper_ink", "Upper_teak", "Window_ink")
LOWER = stl("Lower_blue", "Lower_white", "Lower_ink")
res = {"x_scale": SX}
r3 = lambda v: None if v is None else round(float(v), 3)

# 1 fin tenon in the hull socket (glued)
FIN = stl("Fin_cap"); xs = FIN[:, :, 0]
xf = float(np.mean([v for v in (st.get("fin_x"),) if v is not None])) if st.get("fin_x") else None
rows = []
for z in (-11.8, -10.5, -9.0, -7.6):
    sf = section(FIN, 2, z)
    if not len(sf): continue
    P = sf.reshape(-1, 2); P = P[np.abs(P[:, 1]) < 4]
    cx = 0.5*(P[:, 0].min()+P[:, 0].max())
    sh = section(HULL, 2, z); hw = half_widths(sh, np.array([cx, 0.0]))
    if hw is None: rows.append({"z": z, "socket": "blocked"}); continue
    tx = 0.5*(P[:, 0].max()-P[:, 0].min()); ty = 0.5*(P[:, 1].max()-P[:, 1].min())
    sx_ = 0.5*(hw[0][0]+hw[1][0]); sy = 0.5*(hw[2][0]+hw[3][0])
    rows.append({"z": z, "tenon_len": r3(2*tx), "socket_len": r3(2*sx_), "clear_x_side": r3(sx_-tx),
                 "tenon_thk": r3(2*ty), "socket_w": r3(2*sy), "clear_y_side": r3(sy-ty),
                 "socket_centre_offset_y": r3((hw[2][0]-hw[3][0])/2), "centre_x": r3(cx)})
res["fin_tenon"] = rows
# seating: the fin root (outside the tenon box) against the hull bottom
FP = FIN.reshape(-1, 3); cx = rows[0]["centre_x"]
root = FP[(FP[:, 2] > -16) & (np.abs(FP[:, 0]-cx) > rows[0]["tenon_len"]/2+0.3)]
res["fin_root_top_z"] = r3(root[:, 2].max()) if len(root) else None
res["tenon_top_z"] = r3(FP[(np.abs(FP[:, 0]-cx) < 8)][:, 2].max())
sock_top = None
for z in np.arange(-8.0, -5.0, 0.05):
    if inside(section(HULL, 2, z), np.array([cx, 0.0])): sock_top = z; break
res["socket_ceiling_z"] = r3(sock_top)
# hull outer bottom at fin root (first material along +z from below, at the tenon ends and mid)
def first_hit_z(T, x, y):
    d = section(T, 0, x); h = ray(d, np.array([y, -60.0]), np.array([0.0, 1.0])); return -60+h[0] if len(h) else None
res["hull_bottom_z_at_fin"] = {str(round(dx, 1)): r3(first_hit_z(HULL, cx+dx, 2.0)) for dx in (-12, -9, 0, 9, 12)}

# 2 rudder stock in its bore
RUD = stl("Rudder", "Rudder_ink"); rx = st["rudder_x"]; c0 = np.array([rx, 0.0]); rr = []
for z in [-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.3, 2.7, 3.5, 5.0, 6.5, 8.0, 9.2, 9.7]:
    sh = section(HULL, 2, z); hw = half_widths(sh, c0) if len(sh) else "no hull"
    sr = section(RUD, 2, z); P = sr.reshape(-1, 2) if len(sr) else np.zeros((0, 2))
    P = P[np.hypot((P[:, 0]-rx)/SX, P[:, 1]) < 1.5] if len(P) else P
    st_x = 0.5*(P[:, 0].max()-P[:, 0].min()) if len(P) else None
    st_y = 0.5*(P[:, 1].max()-P[:, 1].min()) if len(P) else None
    if hw is None: rr.append({"z": z, "bore": "BLOCKED"}); continue
    if hw != "no hull" and any(v[0] is None for v in hw): rr.append({"z": z, "bore": "open to the side", "raw": hw}); continue
    if hw == "no hull": rr.append({"z": z, "bore": "below hull", "stock_dx": r3(st_x and 2*st_x), "stock_dy": r3(st_y and 2*st_y)}); continue
    bx = 0.5*(hw[0][0]+hw[1][0]); by = 0.5*(hw[2][0]+hw[3][0])
    rr.append({"z": z, "bore_dx": r3(2*bx), "bore_dy": r3(2*by), "stock_dx": r3(st_x and 2*st_x), "stock_dy": r3(st_y and 2*st_y),
               "clear_x_side": r3(st_x and bx-st_x), "clear_y_side": r3(st_y and by-st_y),
               "bore_centre_off": [r3((hw[0][0]-hw[1][0])/2), r3((hw[2][0]-hw[3][0])/2)]})
res["rudder"] = rr
RP = RUD.reshape(-1, 3); res["stock_top_z"] = r3(RP[:, 2].max())

# 3 wheel stubs in the binnacle bores (axle along x; CA glued)
WS = stl("WheelSpokes_Port"); w = st["wheel"]; c1 = np.array([w["y"], w["z"]]); ww = []
for x in np.arange(-74.0, -69.0, 0.5):
    sw = section(WS, 0, x); P = sw.reshape(-1, 2) if len(sw) else np.zeros((0, 2))
    P = P[np.hypot(P[:, 0]-c1[0], P[:, 1]-c1[1]) < 1.3] if len(P) else P
    sh = section(HULL, 0, x); hw = half_widths(sh, c1) if len(sh) else None
    ww.append({"x": round(float(x), 2), "stub_d": r3(P[:, 0].max()-P[:, 0].min()) if len(P) else None,
               "bore": None if hw is None else [r3(v[0]) for v in hw]})
res["wheel_port"] = ww

# 4 bulb: cup posts in the cap holes (glued after the lead goes in)
CUP = stl("Ballast_cup"); CAP = FIN; b = st["bulb"]; pp = []
for px in b["posts_x"]:
    for z in (b["split_z"]-0.6, b["split_z"]+0.3, b["split_z"]+0.7):
        sc = section(CUP, 2, z); P = sc.reshape(-1, 2); P = P[np.hypot(P[:, 0]-px, P[:, 1]) < 1.6]
        sk = section(CAP, 2, z); hw = half_widths(sk, np.array([px, 0.0])) if len(sk) else None
        pr = 0.5*(P[:, 1].max()-P[:, 1].min()) if len(P) else None
        pp.append({"post_x": r3(px), "z": r3(z), "post_d_y": r3(pr and 2*pr), "post_d_x": r3(P[:, 0].max()-P[:, 0].min()) if len(P) else None,
                   "hole_d_y": None if not hw else r3(hw[2][0]+hw[3][0]), "hole_d_x": None if not hw else r3(hw[0][0]+hw[1][0])})
res["bulb_posts"] = pp
CPP = CUP.reshape(-1, 3); KP = CAP.reshape(-1, 3)
res["cup_top_z"] = r3(CPP[np.abs(CPP[:, 0]-b["posts_x"][0]) > 3][:, 2].max()); res["cap_bottom_z"] = r3(KP[:, 2].min())

json.dump(res, open(f"review14/fits_{V}.json", "w"), indent=1)
for k, v in res.items():
    if isinstance(v, list):
        print(k); [print("  ", r) for r in v]
    else:
        print(k, v)
