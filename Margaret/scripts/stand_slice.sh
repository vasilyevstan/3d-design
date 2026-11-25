#!/bin/bash
# single-colour BambuStudio slice of a bed-placed STL.
# Usage: stand_slice.sh <dir> [stl=Stand-bed.stl] [out=Margaret-stand.3mf] [filament 1-4, default 3 = navy] [plate name]
#   e.g. the display sail: stand_slice.sh <dir> Display_sail-bed.stl Margaret-display-sail.3mf 1 "Margaret display sail"
set -euo pipefail
F="$(cd "$(dirname "$0")" && pwd)"; SD="$1"; STL="${2:-Stand-bed.stl}"; OUT3="${3:-Margaret-stand.3mf}"
FIL="${4:-3}"; NAME="${5:-Margaret stand}"
if [ "$STL" = "Stand-bed.stl" ]; then W="$SD/slice"; else W="$SD/slice-${STL%-bed.stl}"; fi
mkdir -p "$W"; cd "$W"
MARGARET_WORK="$PWD" python3 "$F/prepare_slice.py" > prep.log 2>&1
STL="$STL" NAME="$NAME" python3 - <<'PY'
import json, os
p = json.load(open("process.json"))
p.update(enable_support="0", enable_prime_tower="0", sparse_infill_density="15%", wall_loops="3")
json.dump(p, open("process.json", "w"))
json.dump({"plates": [{"plate_name": os.environ["NAME"], "need_arrange": False, "objects": [
    {"path": os.path.abspath("../" + os.environ["STL"]), "count": 1, "filaments": [1], "assemble_index": [1]}]}]},
    open("plate.json", "w"), indent=1)
PY
cp "f$FIL.json" fn.json
rm -f "$SD/$OUT3"
/Applications/BambuStudio.app/Contents/MacOS/BambuStudio --load-settings "machine.json;process.json" --load-filaments "fn.json" \
    --load-assemble-list plate.json --arrange 0 --orient 0 --slice 1 --export-3mf "$SD/$OUT3" > slice.log 2>&1
rm -rf x && mkdir x && (cd x && unzip -q "$SD/$OUT3")
grep -m4 -i "model printing time\|total estimated time\|total filament weight\|filament used \[g\]" x/Metadata/plate_1.gcode | tee times.txt
echo "SLICE OK $OUT3"
