# Vertical ray-cast every 0.1 mm; compare the z-hits (solid boundaries) of v7m vs v7n per part.
import numpy as np, json
def tris(path):
    d = np.fromfile(path, dtype=np.uint8); n = int(np.frombuffer(d[80:84], np.uint32)[0])
    return np.frombuffer(d[84:84+n*50], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))["v"].astype(np.float64)
G = 0.1; X0, Y0 = -101.0137, -34.0071
NX, NY = int(202/G), int(68/G)
def hits(path, zmax):
    T = tris(path); T = T[T[:, :, 2].min(1) < zmax]
    H = {}
    for a, b, c in T:
        lo = np.minimum(np.minimum(a, b), c); hi = np.maximum(np.maximum(a, b), c)
        i0, i1 = int(np.ceil((lo[0]-X0)/G)), int(np.floor((hi[0]-X0)/G)); j0, j1 = int(np.ceil((lo[1]-Y0)/G)), int(np.floor((hi[1]-Y0)/G))
        if i1 < i0 or j1 < j0: continue
        I, J = np.meshgrid(np.arange(i0, i1+1), np.arange(j0, j1+1)); I, J = I.ravel(), J.ravel()
        px, py = X0+I*G, Y0+J*G
        e1, e2 = b-a, c-a; den = e1[0]*e2[1]-e1[1]*e2[0]
        if abs(den) < 1e-12: continue
        u = ((px-a[0])*e2[1]-(py-a[1])*e2[0])/den; v = (e1[0]*(py-a[1])-e1[1]*(px-a[0]))/den
        ok = (u >= 0) & (v >= 0) & (u+v <= 1)
        z = a[2]+u*e1[2]+v*e2[2]
        for i, j, zz in zip(I[ok], J[ok], z[ok]):
            if zz < zmax: H.setdefault((i, j), []).append(round(zz, 2))
    return {k: sorted(v) for k, v in H.items()}
res = {}
for part, zmax in (("Lower_blue", 99), ("Lower_white", 99), ("Lower_ink", 99), ("Upper_white", 6.5), ("Upper_ink", 6.5), ("Upper_navy", 6.5), ("Upper_teak", 6.5)):
    try:
        a, b = hits("yacht-build/v7m/%s.stl" % part, zmax), hits("yacht-build/v7n/%s.stl" % part, zmax)
    except FileNotFoundError:
        continue
    diff = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
    def xy(k): return X0+k[0]*G, Y0+k[1]*G
    pts = np.array([xy(k) for k in diff]) if diff else np.zeros((0, 2))
    outside = [k for k, p in zip(diff, pts) if not (19 < p[0] < 28 and abs(p[1]) < 4)]
    res[part] = {"columns": len(set(a) | set(b)), "differing": len(diff), "differing_outside_mast_zone": len(outside),
                 "diff_bbox": [round(pts[:, 0].min(), 2), round(pts[:, 0].max(), 2), round(pts[:, 1].min(), 2), round(pts[:, 1].max(), 2)] if len(pts) else None,
                 "examples_outside": [(round(xy(k)[0], 2), round(xy(k)[1], 2), a.get(k), b.get(k)) for k in outside[:4]]}
    print(part, json.dumps(res[part]), flush=True)
json.dump(res, open("yacht-build/v7n/column_compat.json", "w"), indent=1)
