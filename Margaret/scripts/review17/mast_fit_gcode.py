"""As-sliced mast heel vs mast bore (upper and lower hull) from the plate G-code. Usage: python3 review17/mast_fit_gcode.py v7m"""
import json, math, re, sys, numpy as np
V = sys.argv[1]; D = f"yacht-build/{V}"
st = json.load(open(f"{D}/stats.json")); lay = json.load(open(f"{D}/plate/layout.json"))
A = math.pi*(1.75/2)**2
XA = st["rig"]["mast_aft_x"]
off = {k: lay[k]["offset"] for k in lay}
D0, W0 = 3.6, 2.6
CLR = float(__import__("os").environ.get("MAST_CLR", 0.25))   # v7m: 0.15, v7n: 0.25 per side
def load(obj):
    """rev 17: multi-plate 3MF -- segments of the plate that carries obj"""
    segs = []; x = y = 0.0; z = h = None; num = re.compile(r"([XYZE])(-?[\d.]+)")
    for line in open(f"{D}/plate/x/Metadata/plate_{lay[obj].get('plate', 1)}.gcode"):
        if line[0] == ";":
            if line.startswith("; Z_HEIGHT:"): z = float(line.split(":")[1])
            elif line.startswith("; LAYER_HEIGHT:"): h = float(line.split(":")[1])
            continue
        if not (line.startswith("G1") or line.startswith("G0")): continue
        d = dict(num.findall(line.split(";")[0]))
        nx, ny = float(d.get("X", x)), float(d.get("Y", y)); e = float(d.get("E", 0))
        if e > 0 and z is not None and line.startswith("G1"):
            L = math.hypot(nx-x, ny-y)
            if L > 0.02: segs.append((z, h, x, y, nx, ny, e*A/L/h+h*(1-math.pi/4)))
        x, y = nx, ny
    return np.array(segs)
def free(z0, z1, o, dirs, box=4.0):
    """per layer in [z0,z1]: free distance from origin o along each dir to the nearest printed line edge"""
    out = {}
    for zz in sorted(set(S[:, 0][(S[:, 0] > z0) & (S[:, 0] <= z1)])):
        L = S[(S[:, 0] == zz)]
        m = (np.abs((L[:, 2]+L[:, 4])/2-o[0]) < box) & (np.abs((L[:, 3]+L[:, 5])/2-o[1]) < box)
        L = L[m]
        if not len(L): continue
        res = []
        for dx, dy in dirs:
            t = np.arange(0, box, 0.004); P = np.stack([o[0]+dx*t, o[1]+dy*t], 1)
            a = L[:, 2:4]; b = L[:, 4:6]; ab = b-a; ll = (ab**2).sum(1)+1e-12
            u = np.clip(((P[:, None, :]-a[None])*ab[None]).sum(2)/ll, 0, 1)
            q = a[None]+u[..., None]*ab[None]; dist = np.sqrt(((P[:, None, :]-q)**2).sum(2))-L[None, :, 6]/2
            hit = np.where((dist <= 0).any(1))[0]
            res.append(t[hit[0]] if len(hit) else None)
        out[round(zz, 2)] = res
    return out
def summ(name, r, idx_pairs):
    vals = [[v[i]+v[j] for i, j in idx_pairs] if None not in v else None for v in r.values()]
    vals = [v for v in vals if v]
    if not vals: print(name, "no data"); return
    a = np.array(vals); print(name, "layers", len(vals), "min", a.min(0).round(3), "median", np.median(a, 0).round(3))
# --- upper hull bore: identity orientation; origin at the centre of the front semicircle (x = XA + D0 - W0/2)
S = load("Hull_upper"); ou = off["Hull_upper"]; cx = XA+D0-W0/2; ROOF = 99
import pprint
r = free(0.0, 9.0, (cx+ou[0], 0+ou[1]), [(-1, 0), (1, 0), (0, -1), (0, 1)])
r = {k: v for k, v in r.items() if k <= ROOF}
summ("upper bore depth(x)/width(y) designed %.2f/%.2f:" % (D0+2*CLR, W0+2*CLR), r, [(0, 1), (2, 3)]); print({k: [round(a+b,3) if a is not None and b is not None else None for a,b in ((v[0],v[1]),(v[2],v[3]))] for k, v in r.items()})
# lower hull printed flipped about X: bed y = -y + off; the bore is upside down (socket floor at the top)
S = load("Hull_lower"); ol = off["Hull_lower"]
r = free(0.0, 5.6, (cx+ol[0], ol[1]), [(-1, 0), (1, 0), (0, -1), (0, 1)])
summ("lower bore depth(x)/width(y) designed %.2f/%.2f:" % (D0+2*CLR, W0+2*CLR), r, [(0, 1), (2, 3)]); print({k: [round(a+b,3) if a is not None and b is not None else None for a,b in ((v[0],v[1]),(v[2],v[3]))] for k, v in r.items()})
# mast: R(-90,Y): print z = model x - XA (flat aft face down), print x = -model z + off, print y = y + off
S = load("Mast"); om = off["Mast"]; x0, x1 = om[0]-25.0, om[0]+2.0       # model z -2 .. 25 (the socketed heel)
Mz = S[(np.maximum(S[:, 2], S[:, 4]) > x0) & (np.minimum(S[:, 2], S[:, 4]) < x1) & (np.abs(S[:, 3]-om[1]) < 3) & (np.abs(S[:, 5]-om[1]) < 3)]
ys = np.concatenate([Mz[:, 3]-Mz[:, 6]/2, Mz[:, 5]-Mz[:, 6]/2]); ye = np.concatenate([Mz[:, 3]+Mz[:, 6]/2, Mz[:, 5]+Mz[:, 6]/2])
wid = {}
for zz in sorted(set(Mz[:, 0])):
    k = Mz[:, 0] == zz
    lo = np.minimum(Mz[k, 3], Mz[k, 5])-Mz[k, 6]/2; hi = np.maximum(Mz[k, 3], Mz[k, 5])+Mz[k, 6]/2
    wid[round(zz, 2)] = round(hi.max()-lo.min(), 3)
print("mast heel printed width per layer (designed 2.60 max):", wid)
print("mast heel printed depth = top layer z:", max(wid), "(designed 3.60)")
