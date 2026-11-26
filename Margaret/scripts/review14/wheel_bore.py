import sys; sys.argv = ["x", sys.argv[1] if len(sys.argv) > 1 else "v7k"]
exec(open("review14/fits_stl.py").read().split("res = {")[0])
w = st["wheel"]
for side, yy in (("port", w["y"]), ("stbd", -w["y"])):
    c = np.array([yy, w["z"]])
    for x in (-73.0, -72.5, -72.0, -71.5, -71.0, -70.6, -70.3, -70.0, -69.8):
        rep = []
        for n in ("Upper_white", "Upper_ink", "Upper_teak", "Window_ink", "Lower_white"):
            S = section(stl(n), 0, x)
            if not len(S): continue
            d = np.linalg.norm(S.mean(1)-c, axis=1); m = d < 1.6
            if m.any(): rep.append("%s nearest wall r=%.3f (%d segs)" % (n, d[m].min(), m.sum()))
        print(side, "x %.1f" % x, "; ".join(rep) or "no material within r 1.6 (bore open or outside binnacle)")
