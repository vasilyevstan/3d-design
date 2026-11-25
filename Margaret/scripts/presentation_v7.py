"""Margaret v7: views sheet, afloat sheet, paper-sail rigging sheet (PNGs) and 1:1 paper-sail templates (PDF)."""
from pathlib import Path
import json, math, os, sys
from PIL import Image, ImageDraw, ImageFont

W = Path(os.environ["MARGARET_WORK"])        # present_v7 renders (+ float/ subdir from float_v7)
B = Path(os.environ["MARGARET_OUT"])         # yacht-build/<tag> (stats/stability/hydro_check)
D = Path(os.environ["MARGARET_DELIVER"])     # deliverable folder
ST = json.load(open(B / "stats.json"))
SB = json.load(open(B / "stability.json"))
HY = json.load(open(B / "hydro_check.json"))
SLICE = json.loads(os.environ.get("MARGARET_SLICE", "{}"))
TAG = os.environ.get("MARGARET_TAG", B.name)

FONTS = Path("/System/Library/Fonts/Supplemental")
def font(sz, bold=False):
    return ImageFont.truetype(str(FONTS / ("Arial Bold.ttf" if bold else "Arial.ttf")), sz)

def place(canvas, fn, rect):
    im = Image.open(W / fn).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    flat = Image.alpha_composite(bg, im).convert("RGB")
    inv = Image.eval(flat, lambda v: 255 - v)
    box = inv.getbbox() or (0, 0, im.width, im.height)
    flat = flat.crop(box)
    x, y, r, b = rect
    flat.thumbnail((r - x, b - y), Image.Resampling.LANCZOS)
    canvas.paste(flat, (int((x + r - flat.width) / 2), int((y + b - flat.height) / 2)))

navy, muted, sand, paper = "#142f3c", "#425e66", "#e0c299", "#f9f9f2"
TOP_H, BOT_H, HEAD = 760, 500, 131
H = HEAD + 20 + TOP_H + 20 + BOT_H + 92
sheet = Image.new("RGB", (1800, H), "#edf1ee")
d = ImageDraw.Draw(sheet)
d.rectangle((0, 0, 1800, HEAD), fill=navy)
d.text((38, 19), "Margaret", font=font(55, True), fill="#f5f4e9")
d.text((42, 89), "SUN ODYSSEY 43-STYLE   /   200 MM FREE-SAILING MODEL   /   ONE BAMBU P2S PLATE",
       font=font(19), fill="#c5d5d7")
d.text((1760, 57), "DESIGN VIEWS  /  " + TAG, anchor="rm", font=font(20, True), fill=sand)
items = [("Starboard bow quarter", "view-1.png"), ("Port profile", "view-2.png"),
         ("Starboard profile", "view-3.png"), ("Cockpit, twin helms and teak", "view-4.png"),
         ("Deck plan", "view-5.png"), ("Detachable ballast bulb, 3 mm lead", "view-6.png")]
for i, (title, fn) in enumerate(items):
    row, col = divmod(i, 3)
    x = 27 + col * 586
    y = HEAD + 20 + (0 if row == 0 else TOP_H + 20)
    ch = TOP_H if row == 0 else BOT_H
    d.rectangle((x, y, x + 571, y + ch), fill="#ffffff")
    place(sheet, fn, (x + 14, y + 14, x + 557, y + ch - 66))
    d.rectangle((x, y + ch - 54, x + 571, y + ch), fill=paper)
    d.text((x + 15, y + ch - 41), "0%d" % (i + 1), font=font(18, True), fill=muted)
    d.text((x + 58, y + ch - 46), title, font=font(24, True), fill=navy)
sails = ST["sails"]
spec = ("LOA 200.0 mm  /  beam 63.4 mm  /  draft 55.5 mm  /  masthead %.0f mm above waterline  /  "
        "paper main %.0f / %.0f / %.0f cm2  /  lead %.1f g = %d x 3 mm balls (bulb holds %d)  /  all-up %.0f g"
        % (ST["rig"]["mast_top_z"], sails["full"]["area_cm2"], sails["medium"]["area_cm2"], sails["start"]["area_cm2"],
           HY["mass_g"]["lead"], HY["mass_g"]["lead_balls"], SB["lead_capacity_balls_discrete"], HY["mass_g"]["total"]))
d.text((28, H - 76), spec, font=font(18), fill=navy)
foot = "Blue underwater hull  /  white topsides and deck  /  navy trim  /  teak decks  /  printed shroud frame  /  paper sails to sail"
if SLICE:
    foot += "  /  slice %s, %.0f g PLA" % (SLICE["time"], SLICE["grams"])
d.text((28, H - 42), foot, font=font(16), fill=muted)
sheet.save(D / "Margaret-views.png", optimize=True)

# ---------------- 1:1 vector PDF (mm, top-left origin) ----------------
PT = 72 / 25.4
pages = []
cmd = None
def new_page():
    global cmd
    cmd = []; pages.append(cmd)
def line(x, y, X, Y, w=0.2, dash=None):
    s = "[%s] 0 d " % " ".join("%.3f" % (v * PT) for v in dash) if dash else "[] 0 d "
    cmd.append(s + "%.4f w %.4f %.4f m %.4f %.4f l S" % (w * PT, x * PT, (297 - y) * PT, X * PT, (297 - Y) * PT))
def poly(pts, w=0.28):
    for a, b in zip(pts, pts[1:] + pts[:1]):
        line(*a, *b, w)
def gline(x, y, X, Y, w=0.12, g=0.62):
    """Thin grey detail line (sail cloth seams etc.): printed on the paper, so it shows on the cut sail."""
    cmd.append("q %.2f G" % g); line(x, y, X, Y, w); cmd.append("Q")
def label(x, y, s, sz=9, bold=False):
    s = s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    assert all(ord(c) < 128 for c in s), s
    cmd.append("BT /%s %g Tf %.4f %.4f Td (%s) Tj ET" % ("B" if bold else "R", sz, x * PT, (297 - y) * PT, s))
NAVY_RGB = "0.08 0.18 0.26"


def fill(pts, rgb=NAVY_RGB):
    cmd.append("q %s rg %s h f Q" % (rgb, " ".join("%.4f %.4f %s" % (x * PT, (297 - y) * PT, "m" if i == 0 else "l")
                                                   for i, (x, y) in enumerate(pts))))


def ntext(x, y, s, cap, mirror=False, rgb=NAVY_RGB):
    """Helvetica-Bold, cap height `cap` mm, centred on x, baseline y (mm, top-left origin); mirrored reads right-to-left."""
    sz = cap / sail_marks.FONT_CAP_EM * PT
    w = sail_marks.text_width(s, cap)
    x0 = x + w / 2 if mirror else x - w / 2
    cmd.append("q %s rg BT /B 1 Tf %.4f 0 0 %.4f %.4f %.4f Tm (%s) Tj ET Q" % (rgb, -sz if mirror else sz, sz, x0 * PT, (297 - y) * PT, s))


def circle(x, y, r=0.6, w=0.18):
    p = [(x + r * math.cos(t * math.tau / 28), y + r * math.sin(t * math.tau / 28)) for t in range(28)]
    poly(p, w)
    line(x - r - 0.8, y, x - r - 0.2, y, 0.12); line(x + r + 0.2, y, x + r + 0.8, y, 0.12)
    line(x, y - r - 0.8, x, y - r - 0.2, 0.12); line(x, y + r + 0.2, x, y + r + 0.8, 0.12)
def scale_bar(y):
    line(15, y, 65, y, 0.4); line(15, y - 3, 15, y + 3, 0.4); line(65, y - 3, 65, y + 3, 0.4)
    for k in range(1, 5):
        line(15 + 10 * k, y - 1.5, 15 + 10 * k, y + 1.5, 0.25)
    label(70, y + 1.2, "Scale check: this bar must measure exactly 50 mm. Print at 100% / Actual size.", 8)

TACK_Z = ST["sail"]["tack_z"]
AVOID = ST["luff_tie_z_avoid"]
HOUNDS_Z = ST["rig"]["hounds_z"]
TAB_W, TAB_H = 4.5, 5.0
TABLING, SEAM_STEP = 1.2, 24.0          # same cloth layout as the printed display sail (display_sail.py)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sail_marks                       # same number / insignia / reef layout as the printed display sail


def inset2(poly, d):
    """Miter offset of a CCW (u, v) polygon by d inwards."""
    n, lines, out = len(poly), [], []
    for i in range(n):
        (a, b), (c, e) = poly[i], poly[(i + 1) % n]
        k = math.hypot(c - a, e - b)
        lines.append(((a - (e - b) / k * d, b + (c - a) / k * d), (c - a, e - b)))
    for i in range(n):
        (p, r), (q, t) = lines[i - 1], lines[i]
        den = r[0] * t[1] - r[1] * t[0]
        f = ((q[0] - p[0]) * t[1] - (q[1] - p[1]) * t[0]) / den
        out.append((p[0] + f * r[0], p[1] + f * r[1]))
    return out


def clip_seg(a, b, poly):
    """Parts of segment a-b inside polygon (even-odd), as (u, v) pairs."""
    ts = [0.0, 1.0]
    for p, q in zip(poly, poly[1:] + poly[:1]):
        dx, dy, ex, ey = b[0] - a[0], b[1] - a[1], q[0] - p[0], q[1] - p[1]
        den = dx * ey - dy * ex
        if abs(den) < 1e-12:
            continue
        t = ((p[0] - a[0]) * ey - (p[1] - a[1]) * ex) / den
        u = ((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / den
        if 0 <= t <= 1 and 0 <= u <= 1:
            ts.append(t)
    ts.sort()
    out = []
    for t0, t1 in zip(ts, ts[1:]):
        m = (t0 + t1) / 2
        mx, my = a[0] + (b[0] - a[0]) * m, a[1] + (b[1] - a[1]) * m
        inside = False
        for p, q in zip(poly, poly[1:] + poly[:1]):
            if (p[1] > my) != (q[1] > my) and mx < p[0] + (my - p[1]) * (q[0] - p[0]) / (q[1] - p[1]):
                inside = not inside
        if inside and t1 - t0 > 1e-6:
            out.append(((a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0),
                        (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)))
    return out


def cloth(x0, y0, L, F):
    """Grey cloth detail inside the cut line: tabling, cross-cut seams square to the leech, batten pockets, patches."""
    zl = L * (1 - TAB_W / F)
    out = [(0.0, 0.0), (F, 0.0), (TAB_W, zl), (TAB_W, L + TAB_H), (0.0, L + TAB_H)]
    P = lambda q: (x0 + q[0], y0 - q[1])
    tab = inset2(out, TABLING)
    for a, b in zip(tab, tab[1:] + tab[:1]):
        gline(*P(a), *P(b))
    C, Hd = out[1], out[2]
    ll = math.dist(C, Hd)
    dl = ((Hd[0] - C[0]) / ll, (Hd[1] - C[1]) / ll)
    di = (-dl[1], dl[0])                    # square to the leech, into the sail
    if di[0] > 0:
        di = (-di[0], -di[1])
    st = SEAM_STEP * 0.75
    while st < ll - 12.0:
        q = (C[0] + dl[0] * st, C[1] + dl[1] * st)
        for a, b in clip_seg(q, (q[0] + di[0] * 150, q[1] + di[1] * 150), tab):
            gline(*P(a), *P(b), 0.14)
        st += SEAM_STEP
    for k, f in enumerate((0.2, 0.4, 0.6, 0.8)):
        q = (C[0] + dl[0] * ll * f, C[1] + dl[1] * ll * f)
        blen = min(18.0, 0.32 * q[0]) if k < 3 else min(12.0, 0.45 * q[0])
        nx, ny = -di[1] * 0.7, di[0] * 0.7
        e = (q[0] + di[0] * blen, q[1] + di[1] * blen)
        box = [(q[0] + nx, q[1] + ny), (e[0] + nx, e[1] + ny), (e[0] - nx, e[1] - ny), (q[0] - nx, q[1] - ny)]
        for a, b in zip(box, box[1:] + box[:1]):
            gline(*P(a), *P(b), 0.14, 0.5)
    pl = min(13.0, 0.2 * F)
    gline(*P((pl, 0.0)), *P((0.0, pl)))
    gline(*P((F - pl, 0.0)), *P((F + dl[0] * pl, dl[1] * pl)))
    gline(*P((TAB_W, zl - 2.0)), *P((0.0, L - 14.0)))
    # markings: port set reads normally on this (port) face; the starboard set is printed mirrored and higher so it reads
    # correctly through the laminated paper from starboard, like the two number sets on a real main
    mk = sail_marks.layout(L, F)
    for n in mk["numbers"]:
        for s, vb in n["lines"]:
            ntext(x0 + n["uc"], y0 - vb, s, n["cap"], n["mirror"])
    for b in mk["insignia"]["bands"]:
        fill([P(q) for q in b])
    for r in mk["reefs"]:
        for c in (r["luff"], r["leech"]):
            ring = sail_marks.circle(c, r["patch_r"], 48)
            for a, b in zip(ring, ring[1:] + ring[:1]):
                for p, q in clip_seg(a, b, tab):
                    gline(*P(p), *P(q), 0.14)
        for c in r["points"]:
            ring = sail_marks.circle(c, r["point_r"], 16)
            for a, b in zip(ring, ring[1:] + ring[:1]):
                gline(*P(a), *P(b), 0.12)
    return mk


def sail(x0, y0, key, title, clew_note, sub=None):
    """Draw sail with luff on the left at x0 and foot along y0 (tack corner = x0, y0)."""
    s = sails[key]
    L, F = s["luff_mm"], s["foot_mm"]
    zl = L * (1 - TAB_W / F)
    pts = [(x0, y0), (x0 + F, y0), (x0 + TAB_W, y0 - zl), (x0 + TAB_W, y0 - L - TAB_H), (x0, y0 - L - TAB_H)]
    mk = cloth(x0, y0, L, F)
    poly(pts, 0.3)
    line(x0, y0 - L, x0 + TAB_W, y0 - L, 0.12, dash=(0.8, 0.8))
    circle(x0 + 2.2, y0 - L - 2.5)                       # head (headboard tab)
    circle(x0 + 2.2, y0 - 3.0)                           # tack
    circle(x0 + F - 4.0, y0 - 2.5)                       # clew
    head_abs = TACK_Z + L
    ties = []
    z = TACK_Z + 14.0
    while z < head_abs - 9.0 and z < HOUNDS_Z - 8.0:
        bad = next((a for a in AVOID if a[0] - 2.0 <= z <= a[1] + 2.0), None)
        if bad:
            z = bad[1] + 3.0
            continue
        ties.append(z); z += 20.0
    for z in ties:
        circle(x0 + 2.0, y0 - (z - TACK_Z), 0.5)
    for a in AVOID:
        if TACK_Z < a[0] < head_abs:
            ya = y0 - ((a[0] + a[1]) / 2 - TACK_Z)
            line(x0 - 8.5, ya, x0 - 1, ya, 0.15, dash=(0.6, 0.6))
            label(x0 - 8.5, ya - 1.2, "spreader", 5)
    # labels sit BELOW the foot, outside the cut line, so the cut sail carries only the grey cloth detail
    label(x0 - 0.5, y0 + 14, "%s  %.1f cm2" % (title, s["area_cm2"]) + ("  -  " + sub if sub else ""), 9, True)
    label(x0 - 0.5, y0 + 18.5, "luff %.1f mm  /  foot %.1f mm  /  grey and navy = sail detail, cut on the black line" % (L, F), 6.5)
    label(x0 + TAB_W + 1.2, y0 - L - 2.0, "HEAD", 6, True)
    label(x0 - 0.5, y0 + 4.5, "TACK", 6, True)
    label(x0 + F - 9, y0 + 4.5, "CLEW", 6, True)
    label(x0 - 0.5, y0 + 8.5, clew_note, 6.5)
    return ties

page_notes = []
new_page()
label(14, 16, "Margaret", 22, True)
label(14, 23.5, "PAPER MAINSAILS  /  1:1 CUTTING TEMPLATE  /  PAGE 1 OF 2", 9, True)
label(14, 29.5, "Print at 100% (Actual size, no Fit). 80-100 g/m2 paper. Luff edge = left edge; it sits against the aft face of the mast.", 7.5)
ties_full = sail(22, 258, "full", "FULL", "clew -> outermost boom hole (70 mm aft of mast)")
ties_start = sail(118, 258, "start", "START", "clew -> 3rd hole from the boom end (46 mm aft of mast)", "recommended first")
tx = 112
label(tx, 44, "How to fit", 11, True)
fit = ["1. Laminate with MATTE clear tape on both faces (keeps the grey seams).",
       "2. Pierce the marked holes with a pin, then open to ~1 mm.",
       "3. Head: thread through the tab hole. Full sail: tie to the",
       "    masthead hole. Start / medium: tie round the mast just",
       "    ABOVE the upper spreader (the spreader stops it sliding).",
       "4. Luff: small thread loops through each luff hole and round",
       "    the mast. Keep loops off the spreader roots (dashed marks).",
       "5. Tack: lash round the mast just above the boom.",
       "6. Clew: tie down to the matching boom hole; snug, not tight.",
       "7. Sheet: tie a thread to the boom sheet hole, run it down through",
       "    the coachroof sheet eye, set the boom ~15 deg off centre, tie off.",
       "The printed shroud frame holds the mast; the paper only drives.",
       "",
       "Markings: %s %s reads from port; the mirrored, higher set reads" % (sail_marks.CODE, sail_marks.NUMBER),
       "    from starboard through the taped paper, as on a real main."]
for i, t in enumerate(fit):
    label(tx, 51 + 5.2 * i, t, 7.2)
scale_bar(287)

new_page()
label(14, 16, "Margaret", 22, True)
label(14, 23.5, "PAPER MAINSAILS  /  1:1 CUTTING TEMPLATE  /  PAGE 2 OF 2", 9, True)
ties_med = sail(22, 168, "medium", "MEDIUM", "clew -> 2nd hole from the boom end (58 mm aft of mast)")
gy = 40
label(100, gy + 6, "Sail markings (same as the printed display sail)", 9, True)
for i, t in enumerate(["%s %s  -  sail number: code over number, 6.8 mm capitals on the FULL" % (sail_marks.CODE, sail_marks.NUMBER),
                       "    sail (450 mm at 1:66), scaled down on START and MEDIUM.",
                       "Port set lower and reading normally; starboard set higher and printed",
                       "    mirrored, so each reads correctly from its own side.",
                       "Two waves near the head  -  Margaret's insignia, symmetric.",
                       "Grey circles  -  two reef rows: cringle patches at luff and leech,",
                       "    reef points between. Cosmetic: the paper is not reefed.",
                       "Rig: the printed shroud frame and mast socket hold the mast; the",
                       "    printed furled genoa is a display piece - leave it off to sail."]):
    label(100, gy + 12 + 4.6 * i, t, 7)
label(14, 196, "Which sail?", 11, True)
st = SB["sails"]
rows = [("START", "start", "first trials and any breeze you can feel on your face"),
        ("MEDIUM", "medium", "steady light air once trim is sorted"),
        ("FULL", "full", "drifting conditions only; looks right for display")]
for i, (nm, k, use) in enumerate(rows):
    label(14, 203 + 5.5 * i, "%s  %.0f cm2  -  heel ~%.0f deg at 1.5 m/s, ~%.0f deg at 2 m/s  -  %s"
          % (nm, st[k]["area_cm2"], st[k]["heel_deg_at_1.5_mps"], st[k]["heel_deg_at_2.0_mps"], use), 7.2)
label(14, 226, "Trim", 11, True)
for i, t in enumerate(["Sail centre of effort is %.0f mm (full) to %.0f mm (start) ahead of the keel centre - a normal small lead." % (
                           SB["sails"]["full"]["lead_mm_CE_ahead_of_CLR"], SB["sails"]["start"]["lead_mm_CE_ahead_of_CLR"]),
                       "If she bears away, ease the sheet; if she rounds up, sheet in or move the clew one hole forward. Fine-tune",
                       "with the rudder (friction stock). Calculated values; confirm in the tank. Full sail only below ~1.5 m/s."]):
    label(14, 233 + 5 * i, t, 7.2)
scale_bar(287)

def pdf_bytes(pages):
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", None,
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"]
    kids = []
    for p in pages:
        data = ("\n".join(p) + "\n").encode("ascii")
        objs.append(b"<< /Length %d >>\nstream\n" % len(data) + data + b"endstream")
        cn = len(objs)
        objs.append(("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.5f %.5f] /Resources << /Font << /R 3 0 R /B 4 0 R >> >> /Contents %d 0 R >>"
                     % (210 * PT, 297 * PT, cn)).encode())
        kids.append(len(objs))
    objs[1] = ("<< /Type /Pages /Kids [%s] /Count %d >>" % (" ".join("%d 0 R" % k for k in kids), len(kids))).encode()
    pdf = bytearray(b"%PDF-1.4\n"); offs = []
    for n, o in enumerate(objs, 1):
        offs.append(len(pdf)); pdf += b"%d 0 obj\n" % n + o + b"\nendobj\n"
    xref = len(pdf)
    pdf += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for o in offs:
        pdf += b"%010d 00000 n \n" % o
    pdf += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return bytes(pdf)

(D / "Margaret-paper-sails.pdf").write_bytes(pdf_bytes(pages))

# ---------------- afloat sheet: hydro_check equilibrium, water tinted at the exact waterline row ----------------
FL = json.load(open(W / "float" / "float.json"))
WATER = (78, 140, 156)


def afloat(name):
    im = Image.open(W / "float" / (name + ".png")).convert("RGBA")
    row = int(round(FL[name]["waterline_row_px"]))
    base = Image.new("RGBA", im.size, (246, 248, 247, 255))
    out = Image.alpha_composite(base, im).convert("RGB")
    below = out.crop((0, row, im.width, im.height))
    tint = Image.new("RGB", below.size, WATER)
    out.paste(Image.blend(below, tint, 0.45), (0, row))
    ImageDraw.Draw(out).line((0, row, im.width, row), fill=(40, 95, 112), width=3)
    return out, row


fw, fh = 1800, 1180
fs = Image.new("RGB", (fw, fh), "#edf1ee"); fd = ImageDraw.Draw(fs)
fd.rectangle((0, 0, fw, HEAD), fill=navy)
fd.text((38, 19), "Margaret", font=font(55, True), fill="#f5f4e9")
fd.text((42, 89), "AFLOAT  /  CALCULATED EQUILIBRIUM FROM THE EXPORTED STL PARTS AND SLICED MASSES",
        font=font(19), fill="#c5d5d7")
fd.text((1760, 57), "WILL SHE FLOAT?  /  " + TAG, anchor="rm", font=font(20, True), fill=sand)
up, rowu = afloat("float-upright")
up = up.crop((90, 0, up.width - 40, up.height))
up.thumbnail((1080, 900), Image.Resampling.LANCZOS)
fs.paste(up, (27, HEAD + 20))
hl, rowh = afloat("float-heel15")
hl = hl.crop((200, 60, hl.width - 200, hl.height - 20))
hl.thumbnail((640, up.height), Image.Resampling.LANCZOS)
fs.paste(hl, (fw - 27 - hl.width, HEAD + 20))
yb = HEAD + 20 + up.height + 16
fd.rectangle((27, yb, fw - 27, fh - 24), fill="#ffffff")
u = HY["upright"]; c15 = next(c for c in HY["curve"] if c["phi"] == 15)
rows = [
    ("Upright, sail up, %d x 3 mm lead (%.1f g)" % (HY["mass_g"]["lead_balls"], HY["mass_g"]["lead"]),
     "all-up %.1f g = %.1f g printed PLA (sliced) + %.1f g paper/ties/glue + lead.  Waterline sits on the boot stripe:"
     % (HY["mass_g"]["total"], HY["mass_g"]["pla_on_board"], HY["mass_g"]["extras"])),
    ("", "the hull sits %.2f mm deeper than designed, trim %.1f deg bow-down (bow %.1f mm deeper) with the lead poured level."
     % (u["sinkage_below_DWL_mm"], u["trim_deg_bow_down"], u["waterline_shift_bow_mm"])),
    ("15 deg heel (gust)", "righting lever GZ %.1f mm; deck edge stays dry until %.0f deg; water reaches the cockpit only past %.0f deg."
     % (c15["GZ_mm"], HY["immersion_heel_deg"]["deck edge amidships"],
        HY["immersion_heel_deg"]["cockpit sill at the walk-through (water into cockpit)"])),
    ("Stability", "GM %.0f mm; sealed hull self-rights up to %.0f deg (a flooded cockpit past %.0f deg is not modelled);"
     % (HY["GM_mm_small_angle"], HY["AVS_deg"],
        HY["immersion_heel_deg"]["cockpit sill at the walk-through (water into cockpit)"])),
    ("", "pushed fully under, the sealed hull would still lift %.0f g more than she weighs." % HY["reserve_buoyancy_g"]),
    ("Physical check", "weigh the dry boat, add lead until boat + lead = %.0f g; float the sealed hull in a tub: no leaks, stripe level."
     % HY["mass_g"]["total"]),
]
for i, (h, t) in enumerate(rows):
    y = yb + 18 + 31 * i
    if h:
        fd.text((48, y), h, font=font(20, True), fill=navy)
    fd.text((470, y), t, font=font(19), fill=muted if not h else navy)
fs = fs.crop((0, 0, fw, yb + 18 + 31 * len(rows) + 16 + 24))
fs.save(D / "Margaret-afloat.png", optimize=True)

# ---------------- paper-sail rigging sheet: annotate the port profile render (view-2 camera) ----------------
V2_TGT_Z, V2_SCALE, V2_W, V2_H = 95.0, 322.0, 1200, 1500
mmpx = V2_SCALE / max(V2_W, V2_H)


def px(x, z):        # port profile: camera on +y looking -y, so bow (+x) is on the left
    return (V2_W / 2 - x / mmpx, V2_H / 2 - (z - V2_TGT_Z) / mmpx)


rg = ST["rig"]; sl = ST["sail"]; bh = rg["boom_holes_x"]
im = Image.open(W / "view-2.png").convert("RGBA")
art = Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im).convert("RGB")
ad = ImageDraw.Draw(art)
red, blue = (196, 64, 44), (30, 86, 140)


def dot(p, r=9, col=red):
    ad.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), outline=col, width=4)


head = px(sl["luff_x"], rg["masthead_hole_z"]); tack = px(rg["boom_holes_x"]["gooseneck loop"], rg["boom_top_z"])
clew = px(bh["clew"], rg["boom_top_z"]); sh_b = px(bh["mainsheet"], rg["boom_top_z"] - 1.3)
sh_e = px(rg["sheet_eye"][0], rg["sheet_eye"][2])
ties = []
z = sl["tack_z"] + 14.0
while z < sl["head_z"] - 9.0 and z < rg["hounds_z"] - 8.0:
    bad = next((a for a in ST["luff_tie_z_avoid"] if a[0] - 2.0 <= z <= a[1] + 2.0), None)
    if bad:
        z = bad[1] + 3.0; continue
    ties.append(z); z += 20.0
for z in ties:
    dot(px(sl["luff_x"] + 0.5, z), 6, blue)
for p in (head, tack, clew, sh_b, sh_e):
    dot(p)
ad.line((sh_b, sh_e), fill=red, width=3)
callouts = [
    (head, "1  HEAD", "full sail: masthead hole. start/medium: just above the upper spreader"),
    (px(sl["luff_x"] + 0.5, ties[len(ties) // 2]), "2  LUFF", "%d thread loops round the mast, every 20 mm" % len(ties)),
    (tack, "3  TACK", "lash the tack hole round the mast at the gooseneck"),
    (clew, "4  CLEW", "tie down to the boom hole for that sail size (marked on the template)"),
    (sh_e, "5  SHEET", "boom sheet hole -> coachroof eye; tie off ~15 deg out"),
]
canvas = Image.new("RGB", (1900, 1500), "#edf1ee")
art_c = art.crop((150, 40, 1080, 1480))
canvas.paste(art_c, (40, 30))
cd = ImageDraw.Draw(canvas)
cd.text((1010, 40), "FULL SAIL SHOWN", font=font(30, True), fill=navy)
cd.text((1010, 82), "start / medium: same ties, shorter luff; use the holes marked on the template", font=font(20), fill=muted)
ox, oy = 40 - 150, 30 - 40
tx = 1010
ys = [170, 420, 860, 990, 1120]
for (p, h, t), y in zip(callouts, ys):
    q = (p[0] + ox, p[1] + oy)
    cd.line((q, (tx - 20, y + 16)), fill=red, width=2)
    cd.text((tx, y), h, font=font(26, True), fill=navy)
    cd.text((tx, y + 36), t, font=font(21), fill=muted)
cd.rectangle((tx - 10, 1230, 1870, 1470), fill="#ffffff")
notes = ["The mast is held up by its socket and the printed shroud frame,",
         "never by the paper. Laminate the paper with clear tape on both faces.",
         "Start with the START sail (%.0f cm2); FULL (%.0f cm2) only below ~1.5 m/s." % (
             sails["start"]["area_cm2"], sails["full"]["area_cm2"]),
         "The sail (%.1f g) and its ties are included in the %.0f g float budget." % (
             SB["extras_g"]["paper sail 80 g/m2 (full)"], HY["mass_g"]["total"])]
for i, t in enumerate(notes):
    cd.text((tx + 8, 1248 + 52 * i), t, font=font(20), fill=navy)
canvas.save(D / "Margaret-sail-rigging.png", optimize=True)
print("AFLOAT + RIGGING OK rows", rowu, rowh, "ties", [round(v, 1) for v in ties])
print("SHEET+PDF OK ties full", [round(z, 1) for z in ties_full], "start", [round(z, 1) for z in ties_start],
      "medium", [round(z, 1) for z in ties_med])

# ---------------- display stand + display sail sheet (only when stand_v7 / display_sail output and renders exist) ----
SD = B / "stand"
if (SD / "stand.json").exists() and all((W / ("stand-%d.png" % i)).exists() for i in (1, 2, 3)):
    import re
    SJ = json.load(open(SD / "stand.json"))

    def slice_info(path):
        t = path.read_text() if path.exists() else ""
        mt = re.search(r"model printing time: ([^;]+);", t)
        mg = re.search(r"total filament weight \[g\] : ([\d.]+)", t)
        return (mt.group(1).strip(), float(mg.group(1))) if mt and mg else None

    st_slice = slice_info(SD / "slice" / "times.txt")
    DS = B / "dsail"
    DJ = json.load(open(DS / "display_sail.json")) if (DS / "display_sail.json").exists() else None
    ds_slice = slice_info(DS / "slice-Display_sail" / "times.txt")
    has4 = DJ is not None and (W / "stand-4.png").exists()
    has5 = (W / "stand-5.png").exists()
    bs, nk, fk, ck, lo = SJ["base"], SJ["neck"], SJ["fork"], SJ["chock"], SJ["lift_off"]
    PH, RH, R5 = 1000, (440 if has4 else 0), (600 if has5 else 0)
    FOOT = 230 if has4 else 196
    SH = HEAD + 20 + PH + 20 + (R5 + 20 if has5 else 0) + (RH + 20 if has4 else 0) + FOOT
    ss = Image.new("RGB", (1800, SH), "#edf1ee")
    sd = ImageDraw.Draw(ss)
    sd.rectangle((0, 0, 1800, HEAD), fill=navy)
    sd.text((38, 19), "Margaret", font=font(55, True), fill="#f5f4e9")
    sd.text((42, 89), "SWAN-NECK TABLE STAND  /  SEPARATE ONE-COLOUR PRINT  /  NO PINS, NO GLUE, NO SUPPORTS"
            + ("  /  OPTIONAL TWO-COLOUR DISPLAY SAIL" if has4 else ""), font=font(19), fill="#c5d5d7")
    sd.text((1760, 57), "DISPLAY STAND  /  " + TAG, anchor="rm", font=font(20, True), fill=sand)
    y5 = HEAD + 20 + PH + 20
    y2 = y5 + (R5 + 20 if has5 else 0)
    panels = [("On the stand" + (" (printed display sail)" if has4 else ""), "stand-1.png", (27, HEAD + 20, 27 + 700, HEAD + 20 + PH)),
              ("Fork pads under the hull either side of the keel; saddle under the bulb tail", "stand-2.png",
               (747, HEAD + 20, 1773, HEAD + 20 + 490)),
              ("Stand alone: thin oval base + one swan neck, nothing enters the model", "stand-3.png",
               (747, HEAD + 20 + 510, 1773, HEAD + 20 + PH))]
    if has5:
        panels.append(("Port profile: the neck leans %.0f deg up to the fork and stays %.1f mm clear of the bulb nose"
                       % (nk["lean_deg"], nk["gap_to_bulb_nose_mm"]), "stand-5.png", (27, y5, 1773, y5 + R5)))
    if has4:
        panels.append(("Printed display sail: sail number %s %s, wave insignia, reef points, seams, battens (navy second colour)"
                       % (DJ["markings"]["code"], DJ["markings"]["number"]) if DJ.get("markings") else
                       "Optional printed display sail: tabling, cross-cut seams, battens, corner patches (relief on one face)",
                       "stand-4.png", (27, y2, 1773, y2 + RH)))
    for i, (title, fn, (x, y, r, b)) in enumerate(panels):
        sd.rectangle((x, y, r, b), fill="#ffffff")
        place(ss, fn, (x + 14, y + 14, r - 14, b - 66))
        sd.rectangle((x, b - 54, r, b), fill=paper)
        sd.text((x + 15, b - 41), "0%d" % (i + 1), font=font(18, True), fill=muted)
        sd.text((x + 58, b - 46), title, font=font(24, True), fill=navy)
    cs = SJ["stability"]["cases"]
    full = cs["sailing trim (full lead, paper sail)"]; nol = cs["no lead"]
    dsc = cs.get("full lead, printed display sail")
    sx, sy, sz = SJ["size_mm"]
    qs = (full, nol) + ((dsc,) if dsc else ())
    tipj = lambda k: "/".join("%.0f" % q["assembly_tip_deg"][k] for q in qs)
    lines = [
        "Stand %.0f x %.0f x %.0f mm  /  %.1f mm oval base + one swan neck + fork  /  navy PLA, upright, 15%% infill, 3 walls, no supports"
        % (sx, sy, sz, bs["thickness_mm"]) + ("  /  slice %s, %.1f g" % st_slice if st_slice else ""),
        "No pins, no glue: the fork's two pads follow the hull bottom either side of the keel (%.0f mm long, zero gap) and carry her;"
        " the keel root sits in the fork slot with %.1f mm per side, so she cannot roll." % (fk["pads_x"][1] - fk["pads_x"][0],
                                                                                         fk["slot_clearance_mm"]),
        "A low saddle under the bulb tail (%.1f mm clear) stops her sliding aft; the fork's closed front stops her going forward."
        % ck["clearance_mm"],
        "To take her off: %s (checked: %d vertex positions, no contact). To put her on: the reverse."
        % (lo["path"], lo["vertex_checks"]),
        "Calculated, not yet measured (full lead / no lead%s): G is %s mm inside the pads; the whole assembly tips at %s deg sideways,"
        " %s deg forward." % (" / display sail" if dsc else "", "/".join("%.0f" % q["G_margin_to_pads_aft_mm"] for q in qs),
                              tipj("sideways"), tipj("forward")),
    ]
    if has4:
        mk = DJ.get("markings")
        lines.append("Display sail: white PLA %.2f mm, %.1f g%s%s; same outline and holes as the FULL paper sail, tied on with the same thread."
                     " Display only: sail on the water with paper."
                     % (DJ["thickness_mm"], DJ["mass_g"],
                        (", navy %s %s inlaid on port, relief on starboard" % (mk["code"], mk["number"])) if mk else
                        (", %.2f/%.2f mm relief" % (DJ["relief_mm"], DJ["batten_relief_mm"])),
                        (", slice %s" % ds_slice[0]) if ds_slice else ""))
    for k, t in enumerate(lines):
        sd.text((28, SH - FOOT + 22 + k * 34), t, font=font(19 if k == 0 else 17, k == 0), fill=navy if k == 0 else muted)
    ss.save(D / "Margaret-stand.png", optimize=True)
    print("STAND SHEET OK")
