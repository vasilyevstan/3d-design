"""On-board PLA per printed object from a Bambu G-code (supports, prime tower and purge excluded).
Usage: python3 gcode_mass.py plate_1.gcode [names comma-separated in assemble order]
       python3 gcode_mass.py <unzipped 3MF dir>   (rev 17: every plate_N.gcode, names from Metadata/slice_info.config)"""
import glob, math, os, re, sys, json
if os.path.isdir(sys.argv[1]):
    md = os.path.join(sys.argv[1], "Metadata")
    paths = sorted(glob.glob(os.path.join(md, "plate_*.gcode")), key=lambda q: int(re.findall(r"(\d+)\.gcode", q)[0]))
    si = open(os.path.join(md, "slice_info.config")).read()
    idname = {int(a): b for a, b in re.findall(r'identify_id="(\d+)" name="([^"]+)"', si)}
    # a plate with a single object has no object labels in its G-code: attribute it whole to that object
    solo = {}
    for blk in si.split("<plate>")[1:]:
        n = int(re.search(r'key="index" value="(\d+)"', blk).group(1))
        ids_ = [int(a) for a in re.findall(r'identify_id="(\d+)"', blk)]
        if len(ids_) == 1:
            solo[os.path.join(md, "plate_%d.gcode" % n)] = ids_[0]
    names = None
else:
    paths, idname, solo = [sys.argv[1]], None, {}
    names = sys.argv[2].split(",") if len(sys.argv) > 2 else None
A = math.pi*(1.75/2)**2/1000.0      # cm3 per mm of filament
RHO = 1.26
obj, feat, tool = None, None, 0
on, off = {}, {}
ids = []
er = re.compile(r"E(-?[\d.]+)")
def lines():
    global obj
    for path in paths:
        obj = None
        for ln in open(path):
            if path in solo and ln.startswith("; FEATURE:"):
                obj = solo[path]
            yield ln


for line in lines():
    if line.startswith("; start printing object, unique label id:"):
        obj = int(line.split(":")[1]);  ids.append(obj) if obj not in ids else None; continue
    if line.startswith("; total layer number"):
        tool = 0
    if line.startswith("; stop printing object"):
        obj = None; continue
    if line.startswith("; FEATURE:"):
        feat = line.split(":", 1)[1].strip(); continue
    m = re.match(r"^\s*T(\d+)\s*$", line)          # rev 17: the start G-code loads the first filament with an indented T
    if m and int(m.group(1)) < 16:
        tool = int(m.group(1)); continue
    if line[:3] in ("G1 ", "G2 ", "G3 ") and "E" in line:
        cmd = line.split(";")[0]
        m = er.search(cmd)
        if not m or not re.search(r"[XYIJ]-?[\d.]", cmd):      # pure-E lines are retract/unretract, not deposits
            continue
        e = float(m.group(1))
        if e <= 0:
            continue
        g = e*A*RHO
        if obj is not None and feat and not feat.startswith("Support") and feat not in ("Prime tower", "Custom"):
            on.setdefault(obj, {}); on[obj][tool] = on[obj].get(tool, 0)+g
        else:
            k = feat if obj is not None or feat in ("Prime tower", "Custom") else "purge/other"
            off[k] = off.get(k, 0)+g
sid = sorted(on)
res = {"objects": {}, "off_board": {k: round(v, 2) for k, v in off.items()}}
for i, o in enumerate(sid):
    nm = idname.get(o, str(o)) if idname else (names[i] if names and i < len(names) else str(o))
    res["objects"][nm] = {"total_g": round(sum(on[o].values()), 2), "by_tool": {str(t+1): round(v, 2) for t, v in sorted(on[o].items())}}
res["on_board_g"] = round(sum(sum(v.values()) for v in on.values()), 2)
print(json.dumps(res, indent=1))
