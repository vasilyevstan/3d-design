"""rev18: as-sliced masthead slot (mast) and J-tang (furler) from the plate-3 G-code.
Usage: python3 review18/slot_gcode.py v7o  -> yacht-build/<V>/slot_gcode.json"""
import json, math, re, sys, numpy as np
V = sys.argv[1] if len(sys.argv) > 1 else "v7o"; D = f"yacht-build/{V}"
st = json.load(open(f"{D}/stats.json")); fu = st["furler"]; lay = json.load(open(f"{D}/plate/layout.json"))
A = math.pi*(1.75/2)**2
def load(obj):
    segs = []; x = y = 0.0; z = h = None; num = re.compile(r"([XYZE])(-?[\d.]+)")
    for line in open(f"{D}/plate/x/Metadata/plate_{lay[obj]['plate']}.gcode"):
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
def cover(S, zz, P):
    """bool per point P (n,2): inside any printed line of layer zz"""
    L = S[S[:, 0] == zz]
    if not len(L): return np.zeros(len(P), bool), 0
    a, b = L[:, 2:4], L[:, 4:6]; ab = b-a; ll = (ab**2).sum(1)+1e-12
    u = np.clip(((P[:, None, :]-a[None])*ab[None]).sum(2)/ll, 0, 1)
    q = a[None]+u[..., None]*ab[None]; d = np.sqrt(((P[:, None, :]-q)**2).sum(2))-L[None, :, 6]/2
    return (d <= 0).any(1), ((d <= 0).any(0)).sum()
def runs(mask, t):
    out, i = [], 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j+1 < len(mask) and mask[j+1]: j += 1
            out.append((round(t[i], 2), round(t[j], 2))); i = j+1
        else: i += 1
    return out
res = {}
# mast, R(-90,Y): print x = -model z + off_x, print y = model y + off_y, print z = model x + off_z
S = load("Mast"); om = lay["Mast"]["offset"]; sl = fu["slot"]
yy = np.arange(-2.3, 2.1, 0.01)
for name, mz in (("pocket_under_lip_z238.6", 238.6), ("open_above_lip_z240.0", 240.0)):
    P = np.stack([np.full_like(yy, om[0]-mz), yy+om[1]], 1); rows = {}
    for zz in sorted(set(S[:, 0])):
        if zz > 3.2: break
        m, _ = cover(S, zz, P)
        if m.any(): rows[round(zz, 2)] = [(round(a, 2), round(b, 2)) for a, b in runs(m, yy)]
    res["mast_" + name + "_printed_y_runs_by_layer"] = rows
# slot width per layer at the pocket station: gap between the two cheek runs
w = {}
for zz, r in res["mast_pocket_under_lip_z238.6_printed_y_runs_by_layer"].items():
    if len(r) == 2: w[zz] = {"slot": round(r[1][0]-r[0][1]-0.01, 2), "cheeks": (round(r[0][1]-r[0][0]+0.01, 2), round(r[1][1]-r[1][0]+0.01, 2))}
res["mast_slot_width_by_layer"] = w
# furler: print z = model y + 0.6; check the tang layers and the leg's printed width
S = load("Furler"); R = np.array(lay["Furler"]["rotation"])[:3, :3]; of = np.array(lay["Furler"]["offset"])
lx = fu["tang"]["leg_x"]; zleg = fu["tang"]["z"][0]+0.6                    # a line across the leg, 0.6 mm above its bottom
mx = np.arange(lx[0]-0.6, lx[1]+0.6, 0.01)
pts = np.stack([mx, np.full_like(mx, -0.1), np.full_like(mx, zleg)], 1)@R.T+of
legs = {}
for zz in sorted(set(S[:, 0])):
    if zz > 1.6: break
    m, n = cover(S, zz, pts[:, :2])
    legs[round(zz, 2)] = runs(m, mx)
res["furler_leg_printed_model_x_runs_by_layer"] = legs
res["furler_leg_designed_x"] = lx
print(json.dumps(res, indent=1))
json.dump(res, open(f"{D}/slot_gcode.json", "w"), indent=1)
