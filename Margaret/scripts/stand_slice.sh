#!/bin/bash
# single-colour (navy PLA) BambuStudio slice of Stand-bed.stl -> Margaret-stand.3mf
set -euo pipefail
F="$(cd "$(dirname "$0")" && pwd)"; SD="$1"; W="$SD/slice"
mkdir -p "$W"; cd "$W"
MARGARET_WORK="$PWD" python3 "$F/prepare_slice.py" > prep.log 2>&1
python3 - <<'PY'
import json
p = json.load(open("process.json"))
p.update(enable_support="0", enable_prime_tower="0", sparse_infill_density="15%", wall_loops="3")
json.dump(p, open("process.json", "w"))
json.dump({"plates": [{"plate_name": "Margaret stand", "need_arrange": False, "objects": [
    {"path": __import__("os").path.abspath("../Stand-bed.stl"), "count": 1, "filaments": [1], "assemble_index": [1]}]}]},
    open("plate.json", "w"), indent=1)
PY
cp f3.json fn.json
rm -f "$SD/Margaret-stand.3mf"
/Applications/BambuStudio.app/Contents/MacOS/BambuStudio --load-settings "machine.json;process.json" --load-filaments "fn.json" \
    --load-assemble-list plate.json --arrange 0 --orient 0 --slice 1 --export-3mf "$SD/Margaret-stand.3mf" > slice.log 2>&1
rm -rf x && mkdir x && (cd x && unzip -q "$SD/Margaret-stand.3mf")
grep -m4 -i "model printing time\|total estimated time\|total filament weight\|filament used \[g\]" x/Metadata/plate_1.gcode | tee times.txt
echo "STAND SLICE OK"
