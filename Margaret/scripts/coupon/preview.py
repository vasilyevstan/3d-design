# What the slicer lays down: navy (T2) G-code paths of each coupon seen face-on (from outboard), vs the designed inlay
import json, re, sys, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont
O = sys.argv[1]; info = json.load(open(O+"/coupons.json")); S = 40
paths = {nm: [] for nm in info}; tool = None; z = 0; X = Y = None
for line in open(O+"/slice/x/Metadata/plate_1.gcode", errors="ignore"):
    if line.startswith("; Z_HEIGHT:"): z = float(line.split(":")[1])
    elif re.match(r"^T\d+\s*$", line): tool = int(line[1:])
    elif line.startswith(("G1", "G0")):
        mx = re.search(r" X([-\d.]+)", line); my = re.search(r" Y([-\d.]+)", line); me = re.search(r" E([-\d.]+)", line)
        nX = float(mx.group(1)) if mx else X; nY = float(my.group(1)) if my else Y
        if tool == 2 and me and float(me.group(1)) > 0 and X is not None:
            for nm, d in info.items():
                lo, hi = d["lo"], d["hi"]
                if lo[0] <= X <= hi[0] and lo[1] <= Y <= hi[1]: paths[nm].append((X, Y, nX, nY, z))
        X, Y = nX, nY
def stl(p):
    b = open(p, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    return np.frombuffer(b[84:84+n*50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))["v"].reshape(-1, 3, 3)
font = ImageFont.load_default(size=22)
tiles = []
for nm, d in info.items():
    lo, hi = d["lo"], d["hi"]; rot = (hi[0]-lo[0]) > (hi[1]-lo[1])
    u = (lambda x, y: x-lo[0]) if rot else (lambda x, y: hi[1]-y)
    Wd = (hi[0]-lo[0]) if rot else (hi[1]-lo[1]); z0, z1 = 3.6, 7.4
    px = lambda uu, zz: (uu*S, (z1-zz)*S)
    im = Image.new("RGB", (int(Wd*S)*2+30, int((z1-z0)*S)+40), "white"); dr = ImageDraw.Draw(im)
    for t in stl(f"{O}/{nm}_ink.stl"):
        dr.polygon([px(u(p[0], p[1]), p[2]) for p in t], fill=(120, 150, 200))
    off = int(Wd*S)+30
    for (x0, y0, x1, y1, zz) in paths[nm]:
        a = px(u(x0, y0), zz-0.08); b = px(u(x1, y1), zz-0.08)
        dr.line([(a[0]+off, a[1]), (b[0]+off, b[1])], fill=(23, 51, 71), width=int(0.16*S))
        if abs(a[0]-b[0]) < 2: dr.rectangle([a[0]+off-4, a[1]-3, a[0]+off+4, a[1]+3], fill=(23, 51, 71))
    dr.text((6, im.height-34), f"{nm}  design (left)  /  sliced navy paths (right)", fill="black", font=font)
    tiles.append(im)
Wt = max(t.width for t in tiles); sheet = Image.new("RGB", (Wt, sum(t.height+8 for t in tiles)), (230, 230, 230)); y = 0
for t in tiles: sheet.paste(t, (0, y)); y += t.height+8
sheet.save(sys.argv[2]); print("saved", sheet.size)
