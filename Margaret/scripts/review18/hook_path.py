# Furler hook vs masthead cap: parked clearances, assembly paths, and tolerance to a mast that stands high.
# Both parts are prisms along y over the hook's thickness, so the contact problem is 2D in the x-z plane at y = Y0.
import json, sys, numpy as np
V = sys.argv[1] if len(sys.argv) > 1 else "v7n"; D = f"yacht-build/{V}"
st = json.load(open(f"{D}/stats.json")); fu = st["furler"]
def tris(p):
    d = np.fromfile(p, dtype=np.uint8); n = int(np.frombuffer(d[80:84], np.uint32)[0])
    return np.frombuffer(d[84:84+n*50], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))["v"].astype(float)
def section(T, y0, zmin):
    T = T[(T[:, :, 2].max(1) > zmin)]
    segs = []
    for t in T:
        s = t[:, 1]-y0
        if (s > 0).all() or (s < 0).all(): continue
        pts = []
        for i in range(3):
            a, b = t[i], t[(i+1) % 3]; sa, sb = a[1]-y0, b[1]-y0
            if sa*sb < 0: u = sa/(sa-sb); pts.append(a+u*(b-a))
            elif sa == 0: pts.append(a)
        if len(pts) >= 2: segs.append((pts[0][0], pts[0][2], pts[1][0], pts[1][2]))
    return np.array(segs)
def inside(S, P):
    """even-odd test of points P (N,2) against segment soup S (M,4)"""
    x1, z1, x2, z2 = S.T; c = np.zeros(len(P), int)
    for k in range(0, len(P), 4000):
        p = P[k:k+4000]; px, pz = p[:, :1], p[:, 1:]
        cond = (z1 > pz) != (z2 > pz)
        xi = x1+(pz-z1)*(x2-x1)/np.where(z2 == z1, 1e-12, z2-z1)
        c[k:k+4000] = (cond & (px < xi)).sum(1)
    return c % 2 == 1
Y0 = 0.4                                   # inside both the hook (y -0.6..1.4) and the cap
F = section(tris(f"{D}/Furler.stl"), Y0, 228.0)
M = section(tris(f"{D}/Mast.stl"), Y0, 228.0)
fx = np.r_[F[:, 0], F[:, 2]]; mx = np.r_[M[:, 0], M[:, 2]]; mz = np.r_[M[:, 1], M[:, 3]]
cap_top = mz.max(); print("cap x %.2f..%.2f  top z %.2f" % (mx.min(), mx.max(), cap_top))
g = 0.02
X, Z = np.meshgrid(np.arange(16.0, 32.0, g), np.arange(228.0, 246.0, g)); G = np.c_[X.ravel(), Z.ravel()]
inF = inside(F, G); inM = inside(M, G)
Fp = G[inF]; Mp = G[inM]
print("hook/furler cells", len(Fp), "mast cells", len(Mp))
a = np.array(fu["axis_head"])-np.array(fu["axis_foot"]); T = np.array([a[0], a[2]])/np.linalg.norm([a[0], a[2]])
print("stay axis (x,z) per mm up the stay", T.round(4))
Mset = set(map(tuple, np.round(Mp/g).astype(int)))
def overlap(du, dz_mast=0.0, dx=0.0):
    """furler moved by du mm along the stay (+ = up, tab coming out of its pocket) and dx in x; mast raised dz"""
    q = np.round((Fp+[T[0]*du+dx, T[1]*du-dz_mast])/g).astype(int)
    return sum(1 for p in map(tuple, q) if p in Mset)*g*g
# parked clearances: smallest shifts that make contact
for name, vec in (("crown down", (0, -1)), ("aft leg forward", (1, 0)), ("front leg aft", (-1, 0))):
    for k in range(1, 200):
        d = k*g
        q = np.round((Fp+np.array(vec)*d)/g).astype(int)
        if any(p in Mset for p in map(tuple, q)): print("parked clearance, %s: %.2f mm" % (name, d)); break
print("parked overlap mm2:", overlap(0))
print("path A - hook on first, then push the foot tab 2.4 mm down its pocket (furler moves down the stay):")
print("  ", [(round(u, 1), round(overlap(u), 2)) for u in np.arange(2.4, -0.01, -0.3)])
print("path B - sideways slide over the cap with the tab in the pocket: possible iff the parked section is clear (prisms along y)")
print("mast standing high by e mm (furler free to ride up the stay by u <= 2.4 mm, tab still in its pocket):")
for e in (0.0, 0.3, 0.5, 1.0, 1.5, 2.0, 3.0, 5.8):
    ok = [u for u in np.arange(0, 2.41, 0.05) if overlap(u, e) == 0]
    print("   e %.1f  -> %s" % (e, ("fits with the furler %.2f mm up the stay" % ok[0]) if ok else "NO pose fits"))
