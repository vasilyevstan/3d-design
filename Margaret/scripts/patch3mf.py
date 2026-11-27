"""Give every object in a Bambu Studio CLI-assembled 3MF its real name, an object-level filament and per-object
print settings, then drop the stale G-code so the patched project can be re-sliced.

usage: python3 patch3mf.py in.3mf out.3mf objects.json
objects.json: {"<assemble_index>": {"name": "Fin_cap", "extruder": 2, "settings": {"wall_loops": "3", ...}}, ...}

Why: the assemble list puts the filament on each part (volume) only. Single-part objects (Fin_cap, Ballast_cup)
then keep the object default, filament 1 (white), and show and re-slice white in the GUI. The assemble list's
print_params also land on the part, where object settings such as supports are ignored.
"""
import json, re, sys, zipfile

src, dst, spec = sys.argv[1], sys.argv[2], json.load(open(sys.argv[3]))
zin = zipfile.ZipFile(src)
cfg = zin.read("Metadata/model_settings.config").decode()
done = set()


def fix(m):
    head, idx, rest = m.group(1), m.group(2), m.group(3)
    o = spec[idx]
    meta = ['    <metadata key="name" value="%s"/>' % o["name"],
            '    <metadata key="extruder" value="%d"/>' % o["extruder"]]
    meta += ['    <metadata key="%s" value="%s"/>' % kv for kv in sorted(o.get("settings", {}).items())]
    done.add(idx)
    return head + "\n".join(meta) + rest


cfg = re.sub(r'(<object id="\d+">\n)    <metadata key="name" value="assemble_(\d+)"/>(\n)', fix, cfg)
missing = set(spec) - done
if missing:
    sys.exit("objects not found: %s" % sorted(missing))
zout = zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    if re.match(r"Metadata/plate_\d+\.gcode(\.md5)?$", it.filename):
        continue
    data = cfg.encode() if it.filename == "Metadata/model_settings.config" else zin.read(it.filename)
    zout.writestr(it, data)
zout.close()
print("PATCHED", len(done), "objects ->", dst)
