# Transom-name print gates on the real sliced plate (from the v7f challenge round):
#  1) per glyph: every layer whose designed cross-section contains that letter gets navy, max run of misses <= 2 layers
#  2) white skin: behind the inlay, white (T0) beads cover the whole name width in every name layer (gap < 0.1 mm)
# usage: python3 transom_gates.py <yacht-build/vX>
import struct, re, sys, json
import numpy as np
V = sys.argv[1]
off = np.array(json.load(open(V+"/plate/layout.json"))["Hull_upper"]["offset"])


def stl(p):
    b = open(p, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    return np.frombuffer(b[84:84+n*50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))["v"].reshape(-1, 3, 3).astype(float)


def first_hits(T, ys, z):
    """x of entry/exit along +x for rays at (y, z); returns list of hit arrays."""
    v0, e1, e2 = T[:, 0], T[:, 1]-T[:, 0], T[:, 2]-T[:, 0]; d = np.array([1.0, 0, 0]); out = []
    p = np.cross(d, e2); det = (e1*p).sum(1); ok = np.abs(det) > 1e-12; inv = np.where(ok, 1/np.where(ok, det, 1), 0)
    for y in ys:
        s = np.array([-100.0, y, z])-v0; u = (s*p).sum(1)*inv; q = np.cross(s, e1); v = (q*d).sum(1)*inv
        t = (e2*q).sum(1)*inv; m = ok & (u >= 0) & (v >= 0) & (u+v <= 1) & (t > 0)
        out.append(np.unique(np.round(np.sort(t[m]), 5))-100)
    return out


def sel(T):
    c = T.mean(1); return T[(c[:, 0] < -85) & (c[:, 1] > 8.0) & (c[:, 1] < 25) & (c[:, 2] > 6.5) & (c[:, 2] < 12.5)]


INK = sel(stl(V+"/Upper_ink.stl")); WH = sel(stl(V+"/Upper_white.stl"))
P = INK.reshape(-1, 3); Y0, Y1, Z0, Z1 = P[:, 1].min(), P[:, 1].max(), P[:, 2].min(), P[:, 2].max()
G = [l for l in open(V+"/plate/x/Metadata/plate_1.gcode", errors="ignore")]
layers = sorted({round(float(l.split(":")[1]), 2) for l in G if l.startswith("; Z_HEIGHT:")})
band = [zt for zt in layers if Z0 <= (zt-0.08)-off[2] <= Z1]
ys = np.arange(Y0, Y1+1e-6, 0.04)
occ, face = {}, {}
for zt in band:
    zs = (zt-0.08)-off[2]
    h = first_hits(INK, ys, zs); occ[zt] = np.array([len(a) >= 2 for a in h])
    hw = first_hits(WH, ys[::25], zs); hi = first_hits(INK, ys[::25], zs)
    face[zt] = min(min(a[0] for a in hw if len(a)), min([a[0] for a in hi if len(a)] or [99]))
allocc = np.any(np.array(list(occ.values())), axis=0)
glyphs = []; i = 0
while i < len(ys):
    if allocc[i]:
        j = i
        while j+1 < len(ys) and allocc[j+1]: j += 1
        glyphs.append((ys[i], ys[j])); i = j+1
    else: i += 1
glyphs = sorted(glyphs, key=lambda g: -g[0])          # reading order seen from astern = decreasing y
names = ["M", "a1", "r1", "g", "a2", "r2", "e", "t"] if len(glyphs) == 8 else ["g%d" % k for k in range(len(glyphs))]
# gcode navy (T2) and white (T0) segments in the transom name region, model coordinates
segs = {0: {}, 2: {}}; tool = None; z = 0; X = Y = None
xlo, xhi = -93.0, -88.0
for line in G:
    if line.startswith("; Z_HEIGHT:"): z = round(float(line.split(":")[1]), 2)
    elif re.match(r"^T\d+\s*$", line): tool = int(line[1:])
    elif line.startswith(("G1", "G0")):
        mx = re.search(r" X([-\d.]+)", line); my = re.search(r" Y([-\d.]+)", line); me = re.search(r" E([-\d.]+)", line)
        nX = float(mx.group(1)) if mx else X; nY = float(my.group(1)) if my else Y
        if z in occ and tool in segs and me and float(me.group(1)) > 0 and X is not None:
            a = (X-off[0], Y-off[1]); b = (nX-off[0], nY-off[1])
            if all(xlo <= p[0] <= xhi and Y0-1 <= p[1] <= Y1+1 for p in (a, b)):
                segs[tool].setdefault(z, []).append((a, b))
        X, Y = nX, nY


def runs(mask):
    out = []; i = 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j+1 < len(mask) and mask[j+1]: j += 1
            out.append((ys[i], ys[j]+0.04)); i = j+1
        else: i += 1
    return out


rep = {"glyphs": {}, "white": {}}; ok = True; tot_s = tot_m = 0
for gname, (ga, gb) in zip(names, glyphs):
    m = (ys >= ga-1e-6) & (ys <= gb+1e-6); run = best = 0; dl = strokes = missed = 0; bad = []
    for zt in band:
        st = [r for r in runs(occ[zt] & m) if r[1]-r[0] >= 0.1]
        if not st: run = 0; continue
        dl += 1; beads = [(min(a[1], b[1])-0.2, max(a[1], b[1])+0.2) for a, b in segs[2].get(zt, [])]
        miss = sum(1 for s0, s1 in st if not any(min(s1, b1)-max(s0, b0) >= min(0.2, 0.5*(s1-s0)) for b0, b1 in beads))
        strokes += len(st); missed += miss
        if miss: bad.append(zt); run += 1; best = max(best, run)
        else: run = 0
    tot_s += strokes; tot_m += missed
    rep["glyphs"][gname] = {"y": [round(float(ga), 2), round(float(gb), 2)], "design_layers": dl, "strokes": strokes,
                            "missed_strokes": missed, "layers_with_miss": bad, "max_run": best}
    ok &= best <= 2
rep["strokes"] = tot_s; rep["missed_strokes"] = tot_m
NY0, NY1 = min(g[0] for g in glyphs), max(g[1] for g in glyphs)+0.04    # the letters' own extent
for zt in band:
    xi = face[zt]+0.828                      # ink back face
    iv = []
    for a, b in segs[0].get(zt, []):
        if all(xi-0.15 <= p[0] <= xi+0.95 for p in (a, b)):
            iv.append((min(a[1], b[1])-0.2, max(a[1], b[1])+0.2))
    iv.sort(); gaps = []; cur = NY0
    for a, b in iv:
        if a > cur: gaps.append((round(float(cur), 2), round(float(a), 2)))
        cur = max(cur, b)
        if cur >= NY1: break
    if cur < NY1: gaps.append((round(float(cur), 2), round(float(NY1), 2)))
    gmax = max([b-a for a, b in gaps] or [0])
    rep["white"][str(zt)] = {"max_gap": round(float(gmax), 3), "gaps": [g for g in gaps if g[1]-g[0] >= 0.1]}
    ok &= gmax < 0.1
rep["pass"] = bool(ok); rep["n_glyphs"] = len(glyphs); rep["layers"] = band
json.dump(rep, open(V+"/transom_gates.json", "w"), indent=1)
print("glyphs found", len(glyphs), "layers in band", len(band))
for g, r in rep["glyphs"].items(): print(" ", g, r)
print("white-behind max gap per layer:", {k: v["max_gap"] for k, v in rep["white"].items()})
print("PASS" if ok else "FAIL")
