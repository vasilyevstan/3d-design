# rasterise the flat seam faces (z == SEAM) of each half and diff v7m vs v7n
import numpy as np, sys, json
SEAM = 2.5
def tris(path):
    d = np.fromfile(path, dtype=np.uint8)
    n = int(np.frombuffer(d[80:84], np.uint32)[0])
    rec = np.frombuffer(d[84:84+n*50], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    return rec["v"].astype(np.float64)
def seam_mask(paths, xs, ys):
    X, Y = np.meshgrid(xs, ys); P = np.stack([X.ravel(), Y.ravel()], 1); m = np.zeros(len(P), bool)
    for p in paths:
        T = tris(p); T = T[np.all(np.abs(T[:, :, 2]-SEAM) < 1e-3, axis=1)][:, :, :2]
        for a, b, c in T:
            lo = np.minimum(np.minimum(a, b), c); hi = np.maximum(np.maximum(a, b), c)
            sel = np.where((P[:, 0] >= lo[0]) & (P[:, 0] <= hi[0]) & (P[:, 1] >= lo[1]) & (P[:, 1] <= hi[1]))[0]
            if not len(sel): continue
            q = P[sel]
            def cr(u, v, w): return (v[0]-u[0])*(w[:, 1]-u[1])-(v[1]-u[1])*(w[:, 0]-u[0])
            d1, d2, d3 = cr(a, b, q), cr(b, c, q), cr(c, a, q)
            ins = ((d1 >= 0) & (d2 >= 0) & (d3 >= 0)) | ((d1 <= 0) & (d2 <= 0) & (d3 <= 0))
            m[sel[ins]] = True
    return m.reshape(X.shape)
xs = np.arange(-101, 101, 0.05); ys = np.arange(-34, 34, 0.05)
B = "yacht-build/%s/%s.stl"
up_m = seam_mask([B % ("v7m", "Upper_white")], xs, ys); up_n = seam_mask([B % ("v7n", "Upper_white")], xs, ys)
lo_m = seam_mask([B % ("v7m", "Lower_ink")], xs, ys); lo_n = seam_mask([B % ("v7n", "Lower_ink")], xs, ys)
A = 0.05*0.05
def region(mask):
    if not mask.any(): return None
    iy, ix = np.where(mask); return [round(xs[ix.min()], 2), round(xs[ix.max()], 2), round(ys[iy.min()], 2), round(ys[iy.max()], 2)]
res = {}
for nm, a, b in (("upper v7m->v7n", up_m, up_n), ("lower v7m->v7n", lo_m, lo_n), ("v7n upper vs v7m lower", lo_m, up_n)):
    lost, gained = a & ~b, b & ~a
    res[nm] = {"area_a_mm2": round(a.sum()*A, 2), "area_b_mm2": round(b.sum()*A, 2), "lost_mm2": round(lost.sum()*A, 3),
               "lost_bbox": region(lost), "gained_mm2": round(gained.sum()*A, 3), "gained_bbox": region(gained)}
# overhang check: v7n upper seam land that has no v7m lower land under it (outside the mast bore)
print(json.dumps(res, indent=1))
