# v7m vs v7n lower-hull STLs: identical outside the mast zone?
import numpy as np
def tris(path):
    d = np.fromfile(path, dtype=np.uint8); n = int(np.frombuffer(d[80:84], np.uint32)[0])
    return np.frombuffer(d[84:84+n*50], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))["v"].astype(np.float64)
for part in ("Lower_blue", "Lower_white", "Lower_ink", "Upper_white"):
    out = []
    for tag in ("v7m", "v7n"):
        T = tris("yacht-build/%s/%s.stl" % (tag, part))
        keep = ~np.any((T[:, :, 0] > 19) & (T[:, :, 0] < 28) & (np.abs(T[:, :, 1]) < 4), axis=1)
        out.append({tuple(np.round(t, 3).ravel()) for t in T[keep]})
    a, b = out
    print(part, "tris outside mast zone v7m/v7n:", len(a), len(b), "only-v7m:", len(a-b), "only-v7n:", len(b-a))
    d = np.array([list(t) for t in (a ^ b)]).reshape(-1, 3, 3) if (a ^ b) else None
    if d is not None:
        print("   diff bbox x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (d[:, :, 0].min(), d[:, :, 0].max(), d[:, :, 1].min(), d[:, :, 1].max(), d[:, :, 2].min(), d[:, :, 2].max()))
print("-- per-plane area of the differing triangles (retriangulation => equal areas, both orientations)")
def area(T): return 0.5*np.linalg.norm(np.cross(T[:, 1]-T[:, 0], T[:, 2]-T[:, 0]), axis=1)
for part in ("Lower_white", "Lower_ink"):
    S = []
    for tag in ("v7m", "v7n"):
        T = tris("yacht-build/%s/%s.stl" % (tag, part))
        T = T[~np.any((T[:, :, 0] > 19) & (T[:, :, 0] < 28) & (np.abs(T[:, :, 1]) < 4), axis=1)]
        S.append(T)
    a = {tuple(np.round(t, 3).ravel()) for t in S[0]}; b = {tuple(np.round(t, 3).ravel()) for t in S[1]}
    for tag, T, other in (("v7m", S[0], b), ("v7n", S[1], a)):
        d = np.array([t for t in T if tuple(np.round(t, 3).ravel()) not in other])
        flat = np.all(np.abs(d[:, :, 2]-d[:, :1, 2]) < 1e-4, axis=1)
        nz = np.sign(np.cross(d[:, 1]-d[:, 0], d[:, 2]-d[:, 0])[:, 2])
        rows = {}
        for z, s, ar in zip(np.round(d[:, 0, 2], 2), nz, area(d)):
            rows[(z, int(s))] = rows.get((z, int(s)), 0)+ar
        print(part, tag, "non-flat:", int((~flat).sum()), {k: round(v, 3) for k, v in sorted(rows.items())})
