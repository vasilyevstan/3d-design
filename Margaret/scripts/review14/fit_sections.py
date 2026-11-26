"""Cross-sections of the three assembly joints from the exported STLs, v7j (top) vs v7k (bottom)."""
import sys, json, numpy as np
from PIL import Image, ImageDraw, ImageFont
OUTP = sys.argv[1]
F = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20); FS = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
PX = 42
COL = {"hull": (40, 70, 160), "rudder": (200, 60, 40), "fin": (20, 140, 90), "cup": (190, 120, 0)}
def panel(V, kind):
    sys.argv = ["x", V]; g = {}
    exec(open("review14/fits_stl.py").read().split("res = {")[0], g)
    stl, section = g["stl"], g["section"]
    HULL = stl("Lower_blue", "Lower_white", "Lower_ink", "Upper_white", "Upper_ink", "Upper_teak")
    if kind == "rudder":
        ax, c, (u0, u1), (v0, v1), parts = 1, 0.05, (-81.5, -74.0), (-4.0, 11.0), [("hull", HULL), ("rudder", stl("Rudder"))]
    elif kind == "fin":
        ax, c, (u0, u1), (v0, v1), parts = 0, -4.304, (-4.0, 4.0), (-14.0, -5.0), [("hull", HULL), ("fin", stl("Fin_cap"))]
    else:
        ax, c, (u0, u1), (v0, v1), parts = 1, 0.05, (0.9, 6.4), (-47.5, -42.5), [("fin", stl("Fin_cap")), ("cup", stl("Ballast_cup"))]
    W, H = int((u1-u0)*PX), int((v1-v0)*PX)
    im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
    for mm in range(int(np.floor(u0)), int(np.ceil(u1))+1):
        d.line([((mm-u0)*PX, 0), ((mm-u0)*PX, H)], fill=(235, 235, 235))
    for mm in range(int(np.floor(v0)), int(np.ceil(v1))+1):
        d.line([(0, (v1-mm)*PX), (W, (v1-mm)*PX)], fill=(235, 235, 235))
    for name, T in parts:
        for a, b in section(T, ax, c):
            d.line([((a[0]-u0)*PX, (v1-a[1])*PX), ((b[0]-u0)*PX, (v1-b[1])*PX)], fill=COL[name], width=3)
    if kind == "rudder":
        y = (v1-2.5)*PX; d.line([(0, y), (W, y)], fill=(120, 120, 120), width=1); d.text((4, y-20), "hull seam", font=FS, fill=(90, 90, 90))
    return im
lab = {"rudder": "Rudder stock in hull bore (side cut)", "fin": "Fin tenon in hull socket (cross cut)", "cup": "Bulb post in cap hole (side cut)"}
note = {("v7j", "rudder"): "0.05 mm/side all the way, through the seam", ("v7k", "rudder"): "0.2 below seam + lead-in; 0.05 grip above",
        ("v7j", "fin"): "0.20 mm/side (loose: +-4.8 deg roll)", ("v7k", "fin"): "0.10 mm/side (+-2.4 deg)",
        ("v7j", "cup"): "r1.0 in r1.2: 0.18/side printed", ("v7k", "cup"): "r1.05 in r1.2: 0.125/side printed"}
rows = []
for V in ("v7j", "v7k"):
    ims = [panel(V, k) for k in ("rudder", "fin", "cup")]
    rows.append((V, ims))
hmax = max(i.size[1] for _, ims in rows for i in ims); wsum = sum(i.size[0] for i in rows[0][1]) + 4*30
sheet = Image.new("RGB", (wsum, 2*(hmax+90)+60), "white"); d = ImageDraw.Draw(sheet)
d.text((30, 6), "Margaret assembly fits - true STL cross-sections (1 grid square = 1 mm)", font=F, fill="black")
d.text((30, 30), "blue = hull, red = rudder, green = fin, orange = bulb cup", font=FS, fill=(80, 80, 80))
for r, (V, ims) in enumerate(rows):
    x = 30; y0 = 60+r*(hmax+90)
    for k, im in zip(("rudder", "fin", "cup"), ims):
        d.text((x, y0), "%s  %s" % (V, lab[k]), font=FS, fill="black")
        d.text((x, y0+20), note[(V, k)], font=FS, fill=(170, 0, 0) if V == "v7j" else (0, 120, 0))
        sheet.paste(im, (x, y0+45)); d.rectangle([x, y0+45, x+im.size[0]-1, y0+45+im.size[1]-1], outline=(150, 150, 150))
        x += im.size[0]+30
sheet.save(OUTP); print("saved", OUTP, sheet.size)
