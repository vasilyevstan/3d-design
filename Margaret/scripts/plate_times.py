"""Per-plate print time and filament grams from a sliced, unzipped Bambu 3MF (rev 17, multi-plate).
usage: plate_times.py <unzipped 3MF dir>  -> JSON {plate: {time (model printing), total (with heating/calibration), grams[]}}
       plate_times.py times.json          -> "XhYYm on plates 1-3" (total time as Bambu Studio shows it; the boat: hull
                                             halves, keel, rudder, spars, wheels)"""
import glob, json, os, re, sys
a = sys.argv[1]
if os.path.isdir(a):
    out = {}
    for g in sorted(glob.glob(os.path.join(a, "Metadata", "plate_*.gcode"))):
        t = open(g, errors="ignore").read(300000)
        out[re.findall(r"plate_(\d+)\.gcode", g)[0]] = {
            "time": re.search(r"model printing time: ([^;]+);", t).group(1).strip(),
            "total": re.search(r"total estimated time: ([^;\n]+)", t).group(1).strip(),
            "grams": [float(v) for v in re.search(r"total filament weight \[g\] : ([\d.,]+)", t).group(1).split(",")]}
    print(json.dumps(dict(sorted(out.items(), key=lambda kv: int(kv[0]))), indent=1))
else:
    d, s = json.load(open(a)), 0
    for k in ("1", "2", "3"):
        for v, u in re.findall(r"(\d+)([dhms])", d[k].get("total", d[k]["time"])):
            s += int(v)*{"d": 86400, "h": 3600, "m": 60, "s": 1}[u]
    print("%dh%02dm on plates 1-3" % (s//3600, s % 3600//60))
