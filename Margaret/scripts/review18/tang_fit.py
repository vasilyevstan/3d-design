# rev18: furler J-tang in the masthead slot. Parked gaps, sideways play, drop-in, lift to release, settle by
# gravity, and how high the mast may stand before the foot tab loses its pocket. Section plane y = YS (mid tang).
import json, sys, numpy as np
V = sys.argv[1] if len(sys.argv) > 1 else "v7o"; D = f"yacht-build/{V}"
fu = json.load(open(f"{D}/stats.json"))["furler"]
def tris(p):
    d = np.fromfile(p, dtype=np.uint8); n = int(np.frombuffer(d[80:84], np.uint32)[0])
    return np.frombuffer(d[84:84+n*50], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))["v"].astype(float)
def section(T, y0, zmin):
    T = T[(T[:, :, 2].max(1) > zmin)]; segs = []
    for t in T:
        s = t[:, 1]-y0
        if (s > 0).all() or (s < 0).all(): continue
        pts = [t[i]+(s[i]/(s[i]-s[(i+1) % 3]))*(t[(i+1) % 3]-t[i]) for i in range(3) if s[i]*s[(i+1) % 3] < 0]
        if len(pts) >= 2: segs.append((pts[0][0], pts[0][2], pts[1][0], pts[1][2]))
    return np.array(segs)
def inside(S, P):
    x1, z1, x2, z2 = S.T; c = np.zeros(len(P), int)
    for k in range(0, len(P), 4000):
        p = P[k:k+4000]; px, pz = p[:, :1], p[:, 1:]
        xi = x1+(pz-z1)*(x2-x1)/np.where(z2 == z1, 1e-12, z2-z1)
        c[k:k+4000] = (((z1 > pz) != (z2 > pz)) & (px < xi)).sum(1)
    return c % 2 == 1
def yhits(T, x, z):
    """y of every crossing of the line (x, *, z) through the mesh"""
    v0, v1, v2 = T[:, 0], T[:, 1], T[:, 2]; out = []
    for a, b, c in zip(v0, v1, v2):
        P = np.array([[a[0], a[2]], [b[0], b[2]], [c[0], c[2]]]); q = np.array([x, z])
        m = np.array([P[1]-P[0], P[2]-P[0]]).T
        if abs(np.linalg.det(m)) < 1e-12: continue
        u, w = np.linalg.solve(m, q-P[0])
        if u >= 0 and w >= 0 and u+w <= 1: out.append(a[1]+u*(b[1]-a[1])+w*(c[1]-a[1]))
    return sorted(round(y, 3) for y in out)
YS = 0.5*(fu["slot"]["y"][0]+fu["slot"]["y"][1])
TF, TM = tris(f"{D}/Furler.stl"), tris(f"{D}/Mast.stl")
F, M = section(TF, YS, 228.0), section(TM, YS, 228.0)
g = 0.02
X, Z = np.meshgrid(np.arange(17.0, 31.0, g), np.arange(230.0, 244.0, g)); G = np.c_[X.ravel(), Z.ravel()]
Fp, Mp = G[inside(F, G)], G[inside(M, G)]
Mset = set(map(tuple, np.round(Mp/g).astype(int)))
foot = np.array([fu["axis_foot"][0], fu["axis_foot"][2]]); head = np.array([fu["axis_head"][0], fu["axis_head"][2]])
T = (head-foot)/np.linalg.norm(head-foot); N = np.array([T[1], -T[0]])          # N points forward
def pose(P, u=0.0, phi=0.0, lift=0.0):
    """slide u mm up the stay, rotate phi rad about the foot (+ = head forward), raise the mast by lift (= move furler down)"""
    c, s = np.cos(phi), np.sin(phi); R = np.array([[c, s], [-s, c]])       # +phi turns T towards N
    return (P-foot)@R.T+foot+T*u-np.array([0, lift])
def ov(P): return sum(1 for p in map(tuple, np.round(P/g).astype(int)) if p in Mset)*g*g
res = {"section_y": YS, "parked_overlap_mm2": ov(Fp)}
for name, vec in (("down", (0, -1)), ("aft", (-1, 0)), ("forward", (1, 0))):
    for k in range(1, 300):
        if ov(Fp+np.array(vec)*k*g) > 0: res["parked_gap_" + name] = round((k-1)*g, 2); break
tang_x = 0.5*(fu["tang"]["x"][0]+fu["slot"]["x_front"]); tang_z = 0.5*(fu["tang"]["z"][0]+fu["slot"]["top_z"])
res["y_hits_mast_at_tang"] = yhits(TM, tang_x, tang_z); res["y_hits_furler_at_tang"] = yhits(TF, tang_x, tang_z)
L = np.linalg.norm(head-foot)
def lifted(P, dz, fwd=0.0):
    """head lifted dz mm straight up (slide up the stay, turned forward so x holds), then moved fwd mm forward"""
    u = dz/T[1]; return pose(P, u, (-T[0]*u+fwd)/L)
# fitting: tab in the pocket, head held up, tang lowered straight down into the slot
res["drop_in_overlap_mm2_by_lift_mm"] = [(round(d, 1), round(ov(lifted(Fp, d)), 3)) for d in np.arange(2.0, -0.01, -0.1)]
res["drop_in_clear"] = all(o == 0 for _, o in res["drop_in_overlap_mm2_by_lift_mm"])
# captive: a forward push (or a bow-down tilt) only frees the head once it is lifted this far
for k in range(0, 60):
    d = k*0.05
    if all(ov(lifted(Fp, d, f)) == 0 for f in np.arange(0.0, 2.51, 0.1)): break
res["lift_to_release_forward_mm"] = round(d, 2)
# let go 1.8 mm up (and 0.3 mm off line forward): gravity alone, step by step slide down the stay or swing aft
u_, ph_ = 1.8/T[1], (-T[0]*1.8/T[1]+0.3)/L
for _ in range(2000):
    if ov(pose(Fp, u_-g, ph_)) == 0: u_ -= g
    elif ov(pose(Fp, u_, ph_-g/L)) == 0: ph_ -= g/L
    else: break
res["let_go_rest"] = {"u_mm": round(u_, 2), "head_aft_mm": round(-ph_*L, 2)}
# gravity settle from the design pose: largest slide down the stay, then rotate aft, before contact
for k in range(0, 200):
    if ov(pose(Fp, -k*g)) > 0: break
res["settle_down_stay_mm"] = round((k-1)*g, 2); u0 = -(k-1)*g
for k in range(0, 200):
    if ov(pose(Fp, u0, -k*g/L)) > 0: break
res["settle_then_aft_mm"] = round((k-1)*g, 2)
z0 = fu["slot"]["z0"]; band = Fp[(Fp[:, 1] > z0-2.3) & (Fp[:, 1] < z0)]       # lashing zone in front of the cap
for nm, P in (("design", band), ("settled", pose(band, u0, -res["settle_then_aft_mm"]/L))):
    for k in range(0, 200):
        if ov(P-np.array([k*g, 0])) > 0: res["head_gap_to_cap_mm_" + nm] = round((k-1)*g, 2); break
tab = fu["foot_tab"][2]-1.0; floor_gap = fu["stemhead_pocket"][3]-tab
res["tab_in_pocket_mm"] = tab; res["tab_floor_gap_mm_design"] = round(floor_gap, 2)
res["tab_floor_gap_mm_settled"] = round(floor_gap+u0, 2)
hi = []
for e in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
    u = e/T[1]; phi = -T[0]*u/L                     # ride up the stay with the slot; turn the head forward by the
    o = ov(pose(Fp, u, phi, e))                     # aft drift of the slide so the tang keeps its place in the slot
    hi.append({"mast_high_mm": e, "overlap_mm2": round(o, 3), "tab_left_mm": round(tab-u, 2)})
res["mast_high"] = hi
print(json.dumps(res, indent=1))
json.dump(res, open(f"{D}/tang_fit.json", "w"), indent=1)
