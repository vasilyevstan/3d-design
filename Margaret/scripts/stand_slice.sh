#!/bin/bash
# BambuStudio slice of a bed-placed STL (stand, display sail).
# Usage: stand_slice.sh <dir> [stl=Stand-bed.stl] [out=Margaret-stand.3mf] [filament 1-4, default 3 = navy] [plate name]
#   e.g. the display sail: stand_slice.sh <dir> Display_sail-bed.stl Margaret-display-sail.3mf 1 "Margaret display sail"
# If <name>_ink-bed.stl exists next to <name>-bed.stl it is added to the same object as a navy (filament 3) volume and
# the plate becomes two-colour (all four AMS filaments loaded, prime tower kept).
# SUPPORT=1 turns on tree supports that may land on the model (the aft-rising stand's fork head).
set -euo pipefail
F="$(cd "$(dirname "$0")" && pwd)"; SD="$1"; STL="${2:-Stand-bed.stl}"; OUT3="${3:-Margaret-stand.3mf}"
FIL="${4:-3}"; NAME="${5:-Margaret stand}"
if [ "$STL" = "Stand-bed.stl" ]; then W="$SD/slice"; else W="$SD/slice-${STL%-bed.stl}"; fi
mkdir -p "$W"; cd "$W"
MARGARET_WORK="$PWD" python3 "$F/prepare_slice.py" > prep.log 2>&1
INK="${STL%-bed.stl}_ink-bed.stl"; [ -f "$SD/$INK" ] || INK=""
STL="$STL" NAME="$NAME" INK="$INK" FIL="$FIL" SUP="${SUPPORT:-0}" python3 - <<'PY'
import json, os
ink, fil = os.environ["INK"], int(os.environ["FIL"])
p = json.load(open("process.json"))
p.update(enable_support="0", sparse_infill_density="15%", wall_loops="3")
if os.environ["SUP"] == "1":
    p.update(enable_support="1", support_type="tree(auto)", support_on_build_plate_only="0")
if not ink:
    p.update(enable_prime_tower="0")
json.dump(p, open("process.json", "w"))
objs = [{"path": os.path.abspath("../" + os.environ["STL"]), "count": 1, "filaments": [fil if ink else 1], "assemble_index": [1]}]
if ink:
    objs.append({"path": os.path.abspath("../" + ink), "count": 1, "filaments": [3], "assemble_index": [1]})
json.dump({"plates": [{"plate_name": os.environ["NAME"], "need_arrange": False, "objects": objs}]},
    open("plate.json", "w"), indent=1)
PY
if [ -n "$INK" ]; then FILS="f1.json;f2.json;f3.json;f4.json"; else cp "f$FIL.json" fn.json; FILS="fn.json"; fi
rm -f "$SD/$OUT3"
/Applications/BambuStudio.app/Contents/MacOS/BambuStudio --load-settings "machine.json;process.json" --load-filaments "$FILS" \
    --load-assemble-list plate.json --arrange 0 --orient 0 --slice 1 --export-3mf "$SD/$OUT3" > slice.log 2>&1
rm -rf x && mkdir x && (cd x && unzip -q "$SD/$OUT3")
grep -m4 -i "model printing time\|total estimated time\|total filament weight\|filament used \[g\]" x/Metadata/plate_1.gcode | tee times.txt
echo "SLICE OK $OUT3"
