"""rev18: true-scale section through the masthead slot (y = slot centre): furler J-tang seated, lifted, removed.
Usage: python3 review18/joint_section.py v7o out.png"""
import sys, io, contextlib, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
V, OUT = sys.argv[1], sys.argv[2]
sys.argv = [sys.argv[0], V]
with contextlib.redirect_stdout(io.StringIO()):
    import importlib.util
    sp = importlib.util.spec_from_file_location("tf", "review18/tang_fit.py"); tf = importlib.util.module_from_spec(sp); sp.loader.exec_module(tf)
fu, g = tf.fu, tf.g
X0, X1, Z0, Z1 = 20.6, 28.6, 233.6, 242.6
PX = 60                                                     # px per mm
W, H = int((X1-X0)*PX), int((Z1-Z0)*PX)
font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 26)
small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 21)
def mask(P):
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m); r = g*PX/2+0.6
    for x, z in P:
        if X0 <= x <= X1 and Z0 <= z <= Z1:
            u, v = (x-X0)*PX, (Z1-z)*PX; d.rectangle((u-r, v-r, u+r, v+r), fill=255)
    return m.filter(ImageFilter.GaussianBlur(0.8))
def panel(Fp, title, note):
    im = Image.new("RGB", (W, H+90), (236, 239, 242)); body = Image.new("RGB", (W, H), (236, 239, 242))
    body.paste((150, 160, 170), (0, 0), mask(tf.Mp)); body.paste((23, 51, 71), (0, 0), mask(Fp))
    im.paste(body, (0, 70)); d = ImageDraw.Draw(im)
    d.text((14, 10), title, fill=(20, 20, 20), font=font); d.text((14, H+76), note, fill=(40, 40, 40), font=small, anchor="lm")
    return im, d
def xy(x, z): return (x-X0)*PX, (Z1-z)*PX+70
sl = fu["slot"]; lip = sl["lip"]
p1, d1 = panel(tf.Fp, "1  Seated", "gaps: down 0.18, aft 0.20, fwd 0.22 mm")
p2, d2 = panel(tf.lifted(tf.Fp, 1.6), "2  Lift 1.6 mm straight up", "lip cleared; drop-in path is clear")
p3, d3 = panel(tf.lifted(tf.Fp, 1.8, 1.0), "3  Then forward to remove", "fit = the same in reverse")
def vlabel(im, txt, x, z):
    t = Image.new("RGBA", (200, 30), (0, 0, 0, 0)); ImageDraw.Draw(t).text((100, 15), txt, fill=(23, 51, 71), font=small, anchor="mm")
    t = t.rotate(90, expand=True); u, v = xy(x, z); im.paste(t, (int(u-15), int(v-100)), t)
for p in (p1, p2, p3):
    vlabel(p, "aft wall", sl["x0"]-0.4, sl["z0"]+1.0); vlabel(p, "lip", lip["x0"]+lip["t_mm"]/2, lip["top_z"]-0.85)
u, v = xy(X0+0.3, Z1-0.5); d1.line((u, v, u+PX, v), fill=(20, 20, 20), width=4); d1.text((u+PX+10, v), "1 mm", fill=(20, 20, 20), font=small, anchor="lm")
u, v = xy(X1-0.2, Z1-0.5); d1.text((u, v), "forward \u2192", fill=(20, 20, 20), font=small, anchor="rm")
sheet = Image.new("RGB", (3*W+40, H+90), (255, 255, 255))
for i, p in enumerate((p1, p2, p3)): sheet.paste(p, (i*(W+20), 0))
sheet.save(OUT); print("saved", OUT, sheet.size)
