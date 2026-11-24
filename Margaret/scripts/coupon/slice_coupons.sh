#!/bin/bash
set -euo pipefail
C="$(cd "$(dirname "$0")" && pwd)"; O="$C/${1:-out}"; W="$O/slice"; rm -rf "$W"; mkdir -p "$W"; cd "$W"
MARGARET_WORK="$PWD" python3 "$C/../prepare_slice.py"
python3 - "$O" <<'PY'
import json, sys, os
O = sys.argv[1]; info = json.load(open(O+"/coupons.json")); objs = []
for i, nm in enumerate(info, 1):
    objs += [{"path": f"{O}/{nm}_white.stl", "count": 1, "filaments": [1], "assemble_index": [i]},
             {"path": f"{O}/{nm}_ink.stl", "count": 1, "filaments": [3], "assemble_index": [i]}]
json.dump({"plates": [{"plate_name": "coupons", "need_arrange": False, "objects": objs}]}, open("plate.json", "w"), indent=1)
PY
/Applications/BambuStudio.app/Contents/MacOS/BambuStudio --load-settings "machine.json;process.json" \
  --load-filaments "f1.json;f2.json;f3.json;f4.json" --load-assemble-list plate.json --arrange 0 --orient 0 --slice 1 \
  --export-3mf "$W/coupons.3mf" > slice.log 2>&1
mkdir -p x && (cd x && unzip -qo ../coupons.3mf)
echo SLICED
