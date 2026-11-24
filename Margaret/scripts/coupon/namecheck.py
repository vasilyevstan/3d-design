# Name print check on the real sliced plate: per-layer navy (T2) extrusion inside the transom and port-bow name
# boxes, plus a face-on picture of the navy G-code paths (what the printer actually lays down).
# usage: python3 namecheck.py <yacht-build/vX> <out.png>
import struct, re, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
V = sys.argv[1]


def stl(p):
    b = open(p, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    return np.frombuffer(b[84:84+n*50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))["v"].reshape(-1, 3, 3)


T = stl(V+"/Upper_ink.stl"); c = T.mean(1)
off = np.array(json.load(open(V+"/plate/layout.json"))["Hull_upper"]["offset"])
sel = {"transom": (c[:, 0] < -89) & (c[:, 1] > 8.5) & (c[:, 1] < 24.5) & (c[:, 2] > 7.5) & (c[:, 2] < 11.5),
       "bow": (c[:, 0] > 55) & (c[:, 0] < 85) & (c[:, 1] > 12) & (c[:, 2] > 5.5) & (c[:, 2] < 12.5)}
box = {}
for k, m in sel.items():
    P = T[m].reshape(-1, 3); box[k] = (P.min(0)+off, P.max(0)+off, T[m]+off)
paths = {k: [] for k in box}; per = {k: {} for k in box}; tool = None; z = 0; X = Y = None
for line in open(V+"/plate/x/Metadata/plate_1.gcode", errors="ignore"):
    if line.startswith("; Z_HEIGHT:"): z = round(float(line.split(":")[1]), 2)
    elif re.match(r"^T\d+\s*$", line): tool = int(line[1:])
    elif line.startswith(("G1", "G0")):
        mx = re.search(r" X([-\d.]+)", line); my = re.search(r" Y([-\d.]+)", line); me = re.search(r" E([-\d.]+)", line)
        nX = float(mx.group(1)) if mx else X; nY = float(my.group(1)) if my else Y
        if tool == 2 and me and float(me.group(1)) > 0 and X is not None:
            for k, (lo, hi, _) in box.items():
                ins = lambda a, b: lo[0]-0.3 <= a <= hi[0]+0.3 and lo[1]-0.3 <= b <= hi[1]+0.3
                if lo[2]-0.2 <= z <= hi[2]+0.2 and ins(X, Y) and ins(nX, nY):
                    paths[k].append((X, Y, nX, nY, z)); per[k][z] = per[k].get(z, 0)+((nX-X)**2+(nY-Y)**2)**0.5
        X, Y = nX, nY
res = {}
for k, (lo, hi, _) in box.items():
    vals = [per[k].get(z, 0.0) for z in sorted(per[k])]
    res[k] = {"bed_z": [round(float(lo[2]), 2), round(float(hi[2]), 2)], "layers_with_navy": len(vals),
              "min": round(min(vals), 2), "median": round(sorted(vals)[len(vals)//2], 2), "max": round(max(vals), 2),
              "per_layer": {str(z): round(v, 1) for z, v in sorted(per[k].items())}}
# expected layer count from the slicer's own layer list over the ink z-span
lz = sorted({round(float(l.split(":")[1]), 2) for l in open(V+"/plate/x/Metadata/plate_1.gcode", errors="ignore")
             if l.startswith("; Z_HEIGHT:")})
for k, (lo, hi, _) in box.items():
    exp = [z for z in lz if lo[2]+0.05 < z <= hi[2]+0.05]
    res[k]["expected_layers"] = len(exp); res[k]["zero_layers"] = [z for z in exp if per[k].get(z, 0) < 0.05]
    print(k, {q: res[k][q] for q in ("bed_z", "expected_layers", "layers_with_navy", "zero_layers", "min", "median", "max")})
json.dump(res, open(V+"/namecheck.json", "w"), indent=1)

S = 40; font = ImageFont.load_default(size=22); tiles = []
for k, (lo, hi, tris) in box.items():
    if k == "transom":
        u = lambda x, y: hi[1]-y; Wd = hi[1]-lo[1]
    else:
        u = lambda x, y: hi[0]-x; Wd = hi[0]-lo[0]
    z0, z1 = lo[2]-0.3, hi[2]+0.3; px = lambda uu, zz: (uu*S+10, (z1-zz)*S)
    im = Image.new("RGB", (max(int(Wd*S)+20, 820), int((z1-z0)*S)*2+70), "white"); dr = ImageDraw.Draw(im)
    for t in tris:
        dr.polygon([px(u(p[0], p[1]), p[2]) for p in t], fill=(120, 150, 200))
    oy = int((z1-z0)*S)+30
    for (x0, y0, x1, y1, zz) in paths[k]:
        a = px(u(x0, y0), zz-0.08); b = px(u(x1, y1), zz-0.08)
        dr.line([(a[0], a[1]+oy), (b[0], b[1]+oy)], fill=(23, 51, 71), width=int(0.16*S))
        if abs(a[0]-b[0]) < 3: dr.rectangle([a[0]-5, a[1]+oy-3, a[0]+5, a[1]+oy+3], fill=(23, 51, 71))
    dr.text((10, im.height-34), f"{k} name: designed inlay (top) / sliced navy G-code paths (bottom)", fill="black", font=font)
    tiles.append(im)
Wt = max(t.width for t in tiles); sheet = Image.new("RGB", (Wt, sum(t.height+10 for t in tiles)), (225, 225, 225)); y = 0
for t in tiles: sheet.paste(t, (0, y)); y += t.height+10
sheet.save(sys.argv[2]); print("saved", sys.argv[2], sheet.size)
