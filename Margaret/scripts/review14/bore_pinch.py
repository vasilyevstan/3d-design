import math, sys
V = sys.argv[1]; sys.argv = ["x", V]
exec(open("review14/fits_gcode.py").read().split("res = {}")[0])
for k in ("bore_lower", "bore_upper"):
    cx, cy = R[k][:2]; worst = []
    for (z, h, x0, y0, x1, y1, w, f) in seg[k]:
        L = math.hypot(x1-x0, y1-y0)
        for t in (0, 0.5, 1):
            d = math.hypot(x0+(x1-x0)*t-cx, y0+(y1-y0)*t-cy)
            if d < 2.3 and d-w/2 < 1.0: worst.append((round(d-w/2, 3), z, round(L, 4), round(w, 3), f))
    print(V, k, "points with edge r < 1.0:", sorted(set(worst))[:4])
