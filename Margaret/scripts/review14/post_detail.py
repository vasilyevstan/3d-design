import math, sys; sys.argv = ["x", sys.argv[1] if len(sys.argv) > 1 else "v7j"]
exec(open("review14/fits_gcode.py").read().split("res = {}")[0])
for i in range(len(posts)):
    cx, cy = R[f"post{i}"][:2]; per = {}
    for z_, h_, px, py, w, f in samples(seg[f"post{i}"]):
        d = math.hypot(px-cx, py-cy)+w/2
        if d < 1.8: per.setdefault(round(z_, 2), []).append((d, f, round(px-cx, 2), round(py-cy, 2)))
    for z_ in sorted(per):
        v = max(per[z_]); print("post", i, "z", z_, "max r %.3f" % v[0], v[1], "at dx,dy", v[2:], "n", len(per[z_]))
cx, cy = R["post0"][:2]
for (z, h, x0, y0, x1, y1, w, f) in seg["post0"]:
    L = math.hypot(x1-x0, y1-y0); r = max(math.hypot(x0-cx, y0-cy), math.hypot(x1-cx, y1-cy))
    if r+w/2 > 1.15 and r < 1.6: print("post0 seg z", z, "len %.3f" % L, "w %.3f" % w, "centre r %.3f" % r, f)
