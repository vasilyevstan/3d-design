"""Sail markings shared by display_sail.py (printed main) and presentation_v7.py (paper PDF).

Plain Python (no bpy). Sail coordinates (u, v) in mm: u runs aft along the foot from the luff, v up the luff from the
tack. Seen from PORT the luff is on the left, so text that reads normally from port runs in +u.

Sail number: code over number, one set per face, staggered like a real main (starboard set higher). Each set reads
correctly from its own side, so drawn in the port view the starboard set is mirrored. 6.8 mm capitals = the RRS
Appendix G 450 mm minimum for a boat over 11 m, at 1:66. Smaller paper sails scale the marks down (k < 1).
Insignia: two symmetric cosine waves near the head (reads the same from both sides). Two reef rows with luff/leech
cringle patches and reef-point patches. SAIL_CODE / SAIL_NO override the text.
"""
import math, os

CODE = os.environ.get("SAIL_CODE", "MGT").upper()
NUMBER = os.environ.get("SAIL_NO", "43").upper()
CAP = 6.8                       # cap height, mm
FONT_CAP_EM = 0.716             # Arial Bold / Helvetica-Bold cap height per em (metric-compatible faces)
TAB_W, TABLING = 4.5, 1.2
FULL_L, FULL_F = 188.35, 70.5
LEFT = 4.0                      # clear of the luff tie holes (u = 2.0, d 1.0) and the luff tabling
# Helvetica-Bold advance widths (1/1000 em); Arial Bold uses the same metrics
_W = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", (722, 722, 722, 722, 667, 611, 778, 722, 278, 556, 722, 611, 833, 722,
                                             778, 667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611)))
_W.update({c: 556 for c in "0123456789"}); _W[" "] = 278; _W["-"] = 333


def text_width(s, cap):
    return sum(_W.get(c, 600) for c in s) / 1000.0 * cap / FONT_CAP_EM


def chord(L, F, v):
    """Distance from the luff to the leech at height v."""
    zl = L * (1 - TAB_W / F)
    return F - (F - TAB_W) * v / zl if v <= zl else TAB_W


def _wave(uc, vc, w, amp, lam, t, n=48):
    """Closed band of thickness t (normal offset) around v = vc + amp*cos(2pi(u-uc)/lam), u in uc +- w/2."""
    top, bot = [], []
    for i in range(n + 1):
        u = uc - w / 2 + w * i / n
        x = 2 * math.pi * (u - uc) / lam
        v = vc + amp * math.cos(x)
        dv = -amp * 2 * math.pi / lam * math.sin(x)
        k = math.hypot(1.0, dv)
        nu, nv = -dv / k, 1.0 / k
        top.append((u + nu * t / 2, v + nv * t / 2)); bot.append((u - nu * t / 2, v - nv * t / 2))
    # trim the slanted ends back to vertical cuts at uc +- w/2 so the badge is exactly symmetric
    top = [(min(max(u, uc - w / 2), uc + w / 2), v) for u, v in top]
    bot = [(min(max(u, uc - w / 2), uc + w / 2), v) for u, v in bot]
    return bot + top[::-1]          # CCW


def layout(L, F):
    k = min(1.0, L / FULL_L, F / FULL_F)
    cap = CAP * k
    gap = 0.35 * cap                                   # between the code and number lines (2.4 mm at full size)
    block = 2 * cap + gap
    pv = 0.30 * L                                      # port set, bottom of the number line
    sv = pv + block + gap                              # starboard set: higher, no overlap seen against the light
    wid = max(text_width(CODE, cap), text_width(NUMBER, cap))
    right = chord(L, F, sv + block) - TABLING - 2.0 * k        # the higher (starboard) set is the narrower one
    if right - LEFT < wid + 1.0:
        raise ValueError("sail number does not fit (%.1f < %.1f mm)" % (right - LEFT, wid + 1.0))
    uc = (LEFT + right) / 2                                    # both sets on one vertical, as on a real main
    numbers = []
    for face, v0, mirror in (("port", pv, False), ("starboard", sv, True)):
        numbers.append({"face": face, "mirror": mirror, "uc": uc, "cap": cap,
                        "lines": [(CODE, v0 + cap + gap), (NUMBER, v0)],       # (text, baseline v)
                        "u_range": [uc - wid / 2, uc + wid / 2], "v_range": [v0, v0 + block]})
    # insignia: 7.5 x 4.7 mm at full size, scaled to fit the narrow head of the smaller sails
    vc = 0.78 * L
    right = chord(L, F, vc + 2.4 * k) - TABLING - 1.0 * k
    s = min(k, (right - LEFT) / 7.5)
    uc = (LEFT + right) / 2
    bands = [_wave(uc, vc + d * s, 7.5 * s, 0.7 * s, 5.0 * s, 1.1 * s) for d in (-1.1, 1.1)]
    insignia = {"uc": uc, "vc": vc, "w": 7.5 * s, "h": (2.2 + 1.1 + 1.4) * s, "bands": bands}
    # reef rows: cringle patches at luff and leech, reef points evenly between them
    reefs = []
    for f in (0.14, 0.28):
        v = f * L
        c = chord(L, F, v)
        r = 4.0 * k
        n = max(2, int((c - 2 * 6.0 * k) // (8.0 * k)) + 1)
        a, b = 6.0 * k, c - 6.0 * k
        pts = [(a + (b - a) * i / (n - 1), v) for i in range(n)]
        reefs.append({"v": v, "luff": (0.0, v), "leech": (c, v), "patch_r": r, "points": pts, "point_r": 0.8 * k})
    return {"k": k, "numbers": numbers, "insignia": insignia, "reefs": reefs, "code": CODE, "number": NUMBER}


def circle(c, r, n=24):
    return [(c[0] + r * math.cos((i + 0.5) * math.tau / n), c[1] + r * math.sin((i + 0.5) * math.tau / n)) for i in range(n)]
