"""Support extrusion inside the mast bore on plates 1 (upper) and 2 (lower), per feature type.
Usage: python3 review17/support_probe.py v7n"""
import json, re, sys, math
V = sys.argv[1]; D = f"yacht-build/{V}"
st = json.load(open(f"{D}/stats.json")); lay = json.load(open(f"{D}/plate/layout.json"))
XA = st["rig"]["mast_aft_x"]; cx = XA+1.8          # bore centre (export x), half-length ~2.05, half-width ~1.55
out = {}
for obj, sgn in (("Hull_upper", 1), ("Hull_lower", -1)):
    o = lay[obj]["offset"]; bx, by = cx+o[0], o[1]           # lower is flipped about x: y -> -y (bore on y = 0)
    feats = {}; z = None; feat = ""; x = y = 0.0; e_by_z = {}
    for line in open(f"{D}/plate/x/Metadata/plate_{lay[obj]['plate']}.gcode"):
        if line.startswith("; Z_HEIGHT:"): z = round(float(line.split(":")[1]), 2); continue
        if line.startswith("; FEATURE:"): feat = line.split(":", 1)[1].strip(); continue
        if not line.startswith("G1"): continue
        mx = re.search(r" X([-\d.]+)", line); my = re.search(r" Y([-\d.]+)", line); me = re.search(r" E([-\d.]+)", line)
        nx = float(mx.group(1)) if mx else x; ny = float(my.group(1)) if my else y
        if me and float(me.group(1)) > 0 and abs((x+nx)/2-bx) < 1.9 and abs((y+ny)/2-by) < 1.4:
            L = math.hypot(nx-x, ny-y); feats[feat] = feats.get(feat, 0)+L
            e_by_z.setdefault(z, {}); e_by_z[z][feat] = e_by_z[z].get(feat, 0)+L
        x, y = nx, ny
    sup = {k: round(v, 1) for k, v in feats.items() if "upport" in k}
    zs = sorted(e_by_z)
    out[obj] = {"plate": lay[obj]["plate"], "inside_bore_mm_by_feature": {k: round(v, 1) for k, v in feats.items()},
                "support_mm": sup, "first_z_with_material_inside": zs[0] if zs else None,
                "first_layers": {str(z_): {k: round(v, 1) for k, v in e_by_z[z_].items()} for z_ in zs[:3]}}
    print(obj, json.dumps(out[obj]))
json.dump(out, open(f"{D}/support_probe.json", "w"), indent=1)
