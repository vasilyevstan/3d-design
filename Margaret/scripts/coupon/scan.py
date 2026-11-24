import json, re, sys
O = sys.argv[1]; info = json.load(open(O+"/coupons.json"))
seg = {}; tool = None; z = 0; X = Y = None
for line in open(O+"/slice/x/Metadata/plate_1.gcode", errors="ignore"):
    if line.startswith("; Z_HEIGHT:"): z = round(float(line.split(":")[1]), 2)
    elif re.match(r"^T\d+\s*$", line): tool = int(line[1:])
    elif line.startswith(("G1", "G0", "G2", "G3")):
        mx = re.search(r" X([-\d.]+)", line); my = re.search(r" Y([-\d.]+)", line); me = re.search(r" E([-\d.]+)", line)
        nX = float(mx.group(1)) if mx else X; nY = float(my.group(1)) if my else Y
        if me and float(me.group(1)) > 0 and X is not None:
            for nm, d in info.items():
                lo, hi = d["lo"], d["hi"]
                if lo[0] <= X <= hi[0] and lo[1] <= Y <= hi[1] and lo[0] <= nX <= hi[0] and lo[1] <= nY <= hi[1]:
                    k = seg.setdefault(nm, {}).setdefault(z, {}); L = ((nX-X)**2+(nY-Y)**2)**0.5
                    k[tool] = k.get(tool, 0)+L
        X, Y = nX, nY
for nm, d in info.items():
    z0, z1 = d["ink_z"]; rows = [(z, v.get(2, 0.0)) for z, v in sorted(seg.get(nm, {}).items()) if z0+0.1 <= z <= z1]
    vals = [r[1] for r in rows]
    print(f"{nm:12s} size {d['size']} depth {d['depth']} off {d['offset']}: layers {len(vals)} zero {sum(v < 0.05 for v in vals)} "
          f"<1.5mm {sum(v < 1.5 for v in vals)} min {min(vals):.1f} median {sorted(vals)[len(vals)//2]:.1f} max {max(vals):.1f}")
    if "-v" in sys.argv: print("   ", " ".join(f"{z}:{v:.1f}" for z, v in rows))
