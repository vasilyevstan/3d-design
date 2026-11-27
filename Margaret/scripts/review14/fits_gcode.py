"""Printed (sliced) size of every glued/sliding joint, from the toolpaths in the plate G-code.
Edge of a printed line = toolpath centre +/- w/2, with w from the extruded volume (Bambu flow model:
area = w*h - h*h + pi*h*h/4). Usage: python3 review14/fits_gcode.py v7j"""
import json, math, re, sys, numpy as np
V = sys.argv[1] if len(sys.argv) > 1 else "v7j"
D = f"yacht-build/{V}"
st = json.load(open(f"{D}/stats.json")); lay = json.load(open(f"{D}/plate/layout.json"))
A = math.pi*(1.75/2)**2
off = {k: lay[k]["offset"] for k in lay}
rx = st["rudder_x"]; fin_cx = -4.304; SX = st["x_scale"]
posts = st["bulb"]["posts_x"]
# regions: name -> (cx, cy, half-box, zmin, zmax) in bed coordinates
R = {"bore_lower": (rx+off["Hull_lower"][0], off["Hull_lower"][1], 2.4, 0.0, 5.6),
     "bore_upper": (rx+off["Hull_upper"][0], off["Hull_upper"][1], 2.4, 0.0, 7.1),
     "stock": (None, None, None, 0.0, 2.2),
     "socket": (fin_cx+off["Hull_lower"][0], off["Hull_lower"][1], 11.0, 9.4, 14.5),
     "tenon": (fin_cx+off["Fin_cap"][0], off["Fin_cap"][1], 11.0, 33.0, 37.8)}
for i, px in enumerate(posts):
    R[f"post{i}"] = (px+off["Ballast_cup"][0], off["Ballast_cup"][1], 1.8, 10.5, 11.5)
    R[f"hole{i}"] = (px+off["Fin_cap"][0], off["Fin_cap"][1], 2.0, 0.0, 1.3)
stock_y = rx+off["Rudder"][1]; stock_x = (off["Rudder"][0]-2.0, off["Rudder"][0]+8.0)   # model z -2..8
seg = {k: [] for k in R}
x = y = 0.0; z = h = None; feat = ""
num = re.compile(r"([XYZEIJ])(-?[\d.]+)")
def add(x0, y0, x1, y1, e):
    L = math.hypot(x1-x0, y1-y0)
    if L < 0.02 or z is None: return    # width from e/L is meaningless on sub-0.02 mm stubs (seam/arc starts)
    w = e*A/L/h+h*(1-math.pi/4)
    mx, my = 0.5*(x0+x1), 0.5*(y0+y1)
    for k, (cx, cy, hb, z0, z1) in R.items():
        if k not in ACTIVE or not (z0 < z <= z1+1e-6): continue
        if k == "stock":
            if stock_x[0] < mx < stock_x[1] and abs(my-stock_y) < 2.0: seg[k].append((z, h, x0, y0, x1, y1, w, feat))
        elif abs(mx-cx) < hb and abs(my-cy) < hb: seg[k].append((z, h, x0, y0, x1, y1, w, feat))
# rev 17: multi-plate 3MF -- read every region from the G-code of the plate its object is on
OWNER = {"bore_lower": "Hull_lower", "bore_upper": "Hull_upper", "stock": "Rudder", "socket": "Hull_lower", "tenon": "Fin_cap"}
OWNER.update({k: ("Ballast_cup" if k.startswith("post") else "Fin_cap") for k in R if k.startswith(("post", "hole"))})
for PL in sorted({lay[o].get("plate", 1) for o in OWNER.values()}):
  ACTIVE = {k for k, o in OWNER.items() if lay[o].get("plate", 1) == PL}
  x = y = 0.0; z = h = None; feat = ""
  for line in open(f"{D}/plate/x/Metadata/plate_{PL}.gcode"):
      if line[0] == ";":
          if line.startswith("; Z_HEIGHT:"): z = float(line.split(":")[1])
          elif line.startswith("; LAYER_HEIGHT:"): h = float(line.split(":")[1])
          elif line.startswith("; FEATURE:"): feat = line.split(":", 1)[1].strip()
          continue
      c = line[:3]
      if c not in ("G1 ", "G0 ", "G2 ", "G3 "): continue
      v = dict(num.findall(line.split(";")[0]))
      nx = float(v.get("X", x)); ny = float(v.get("Y", y)); e = float(v.get("E", 0))
      if c in ("G2 ", "G3 ") and "I" in v:
          ccx, ccy = x+float(v["I"]), y+float(v.get("J", 0)); r = math.hypot(x-ccx, y-ccy)
          a0 = math.atan2(y-ccy, x-ccx); a1 = math.atan2(ny-ccy, nx-ccx)
          if c == "G2 ":
              if a1 >= a0: a1 -= 2*math.pi
          elif a1 <= a0: a1 += 2*math.pi
          n = max(2, int(abs(a1-a0)*r/0.1)); pts = [(ccx+r*math.cos(a0+(a1-a0)*i/n), ccy+r*math.sin(a0+(a1-a0)*i/n)) for i in range(n+1)]
          if e > 0 and not feat.startswith("Support"):
              for (p, q) in zip(pts, pts[1:]): add(p[0], p[1], q[0], q[1], e/n)
      elif e > 0 and ("X" in v or "Y" in v) and not feat.startswith("Support"):
          add(x, y, nx, ny, e)
      x, y = nx, ny

def samples(rows):
    out = []
    for z_, h_, x0, y0, x1, y1, w, f in rows:
        n = max(1, int(math.hypot(x1-x0, y1-y0)/0.04))
        for i in range(n+1):
            out.append((z_, h_, x0+(x1-x0)*i/n, y0+(y1-y0)*i/n, w, f))
    return out
res = {}
def hole(k, label):
    cx, cy = R[k][:2]; per = {}
    for z_, h_, px, py, w, f in samples(seg[k]):
        dx, dy = px-cx, py-cy; d = math.hypot(dx, dy)
        if d > 2.3: continue
        p = per.setdefault(round(z_, 2), {"min": 9, "x": 9, "y": 9, "w": w, "feat": f})
        if d-w/2 < p["min"]: p["min"], p["w"], p["feat"] = d-w/2, w, f
        if abs(dy) < 0.2: p["x"] = min(p["x"], abs(dx)-w/2)
        if abs(dx) < 0.2: p["y"] = min(p["y"], abs(dy)-w/2)
    zs = sorted(per)
    res[label] = {"layers": len(zs), "z_range": [zs[0], zs[-1]] if zs else None,
                  "min_radius": round(min(per[z_]["min"] for z_ in zs), 3),
                  "median_min_radius": round(float(np.median([per[z_]["min"] for z_ in zs])), 3),
                  "radius_along_boat_x": round(float(np.median([per[z_]["x"] for z_ in zs if per[z_]["x"] < 9])), 3),
                  "radius_across_y": round(float(np.median([per[z_]["y"] for z_ in zs if per[z_]["y"] < 9])), 3),
                  "first_layer": {k2: (round(v2, 3) if isinstance(v2, float) else v2) for k2, v2 in per[zs[0]].items()},
                  "hole_wall_feature": per[zs[len(zs)//2]]["feat"]}
hole("bore_lower", "rudder_bore_lower_half"); hole("bore_upper", "rudder_bore_upper_half")
for i in range(len(posts)): hole(f"hole{i}", f"bulb_post_hole_{i}")
# posts: printed outer radius
for i in range(len(posts)):
    cx, cy = R[f"post{i}"][:2]; m = []
    for z_, h_, px, py, w, f in samples(seg[f"post{i}"]):
        d = math.hypot(px-cx, py-cy)
        if d < 1.6: m.append((z_, d+w/2, abs(px-cx)+w/2, abs(py-cy)+w/2))
    res[f"bulb_post_{i}"] = {"layers": len(set(a[0] for a in m)), "max_radius": round(max(a[1] for a in m), 3),
                             "half_x": round(max(a[2] for a in m), 3), "half_y": round(max(a[3] for a in m), 3)}
# fin socket (hole) and tenon (pin): half-width across (y) and half-length (x)
def rect(k, inner):
    cx, cy = R[k][:2]; per = {}
    for z_, h_, px, py, w, f in samples(seg[k]):
        dx, dy = px-cx, py-cy; p = per.setdefault(round(z_, 2), {"+y": None, "-y": None, "+x": None, "-x": None})
        if abs(dx) < 8.0 and abs(dy) < 2.7:
            key = "+y" if dy > 0 else "-y"; val = abs(dy)-w/2 if inner else abs(dy)+w/2
            if p[key] is None or (inner and val < p[key]) or (not inner and val > p[key]): p[key] = val
        if abs(dy) < 1.0 and abs(dx) < 10.6:
            key = "+x" if dx > 0 else "-x"; val = abs(dx)-w/2 if inner else abs(dx)+w/2
            if p[key] is None or (inner and val < p[key]) or (not inner and val > p[key]): p[key] = val
    zs = sorted(z_ for z_ in per if None not in per[z_].values())
    med = {kk: round(float(np.median([per[z_][kk] for z_ in zs])), 3) for kk in ("+y", "-y", "+x", "-x")}
    return {"layers": len(zs), "z_range": [zs[0], zs[-1]], "median_half": med,
            "width_y": round(med["+y"]+med["-y"], 3), "length_x": round(med["+x"]+med["-x"], 3)}
res["fin_socket"] = rect("socket", True); res["fin_tenon"] = rect("tenon", False)
# rudder stock lying on its side: per layer width (bed y) and the layer's z band; worst corner vs the bore ellipse
cz = 1.0; per = {}
for z_, h_, px, py, w, f in samples(seg["stock"]):
    p = per.setdefault(round(z_, 2), [h_, 9e9, -9e9])
    p[1] = min(p[1], py-w/2); p[2] = max(p[2], py+w/2)
bx, by = 1.05*SX, 1.05
rows = []; worst = 9
for z_ in sorted(per):
    h_, y0, y1 = per[z_]; zb, zt = z_-h_, z_
    half = max(y1-stock_y, stock_y-y0)
    for zz in (zb, zt):
        rho = math.hypot(half/bx, (zz-cz)/by); worst = min(worst, (1-rho)*1.05)
    nom = 2*SX*math.sqrt(max(0, 1-((zb+zt)/2-cz)**2))
    rows.append({"z": z_, "printed_width": round(y1-y0, 3), "nominal_chord": round(nom, 3), "off_centre": round((y0+y1)/2-stock_y, 3)})
res["rudder_stock"] = {"layers": rows, "printed_height": round(max(per), 3), "max_width": round(max(r["printed_width"] for r in rows), 3),
                       "worst_corner_margin_to_nominal_bore_mm": round(worst, 3)}
json.dump(res, open(f"review14/fits_gcode_{V}.json", "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "rudder_stock"}, indent=1))
print("rudder_stock", {k: v for k, v in res["rudder_stock"].items() if k != "layers"})
for r in res["rudder_stock"]["layers"]: print("  ", r)
