#!/bin/bash
# full v7 pipeline after build+check: plate, slice, mass, hydro, stability, renders, sheets, close-ups
# usage: run_chain.sh <tag>   e.g. v7d -> yacht-build/v7d, stage7d, /tmp/m7d/deliv
set -euo pipefail
F="$(cd "$(dirname "$0")" && pwd)"; T="$1"
V="$F/yacht-build/$T"; S="$F/stage${T#v}"; DL="/tmp/m${T#v}/deliv"
B=/Applications/Blender.app/Contents/MacOS/Blender
BS=/Applications/BambuStudio.app/Contents/MacOS/BambuStudio
mkdir -p "$S/render" "$DL"
echo "== plate"; MARGARET_OUT="$V" $B -b --factory-startup -P "$F/plate_v7.py" > "$V/plate.log" 2>&1
cd "$V/plate"
echo "== slice"; MARGARET_WORK="$PWD" python3 "$F/prepare_slice.py" > prep.log 2>&1
rm -f Margaret-P2S.3mf assembled.3mf patched.3mf
# rev 17: assemble all plates (no slice), give objects real names / object filament / per-object settings, slice all
$BS --load-settings "machine.json;process.json" --load-filaments "f1.json;f2.json;f3.json;f4.json" \
    --load-assemble-list plate.json --arrange 0 --orient 0 --export-3mf "$PWD/assembled.3mf" > assemble.log 2>&1
python3 "$F/patch3mf.py" assembled.3mf patched.3mf objects.json
$BS --slice 0 --export-3mf "$PWD/Margaret-P2S.3mf" "$PWD/patched.3mf" > slice.log 2>&1
rm -rf x && mkdir x && (cd x && unzip -q ../Margaret-P2S.3mf)
python3 "$F/gcode_mass.py" x > mass.json
python3 "$F/plate_times.py" x > times.json
cat times.json
cd "$F"
PLA=$(python3 -c "import json;d=json.load(open('$V/plate/mass.json'));print(round(sum(o['total_g'] for k, o in d['objects'].items() if k not in ('Stand', 'Display_sail')),2))")
echo "== hydro (PLA $PLA g)"
MARGARET_OUT="$V" SLICE_MASS="$V/plate/mass.json" POUR_TILT=0 HYDRO_JSON="$V/hydro_check.json" python3 hydro_check.py > "$V/hydro.log" 2>&1
echo "== stability"; MARGARET_OUT="$V" PLA_G="$PLA" SLICE_MASS="$V/plate/mass.json" $B -b --factory-startup -P stability_v7.py > "$V/stab.log" 2>&1
echo "== present"; MARGARET_OUT="$V" MARGARET_DELIVER="$S" MARGARET_WORK="$S/render" $B -b "$V/Margaret.blend" -P present_v7.py > "$S/present.log" 2>&1
echo "== float"; MARGARET_OUT="$V" FLOAT_OUT="$S/float" $B -b "$S/Margaret.blend" -P float_v7.py > "$S/float.log" 2>&1
ln -sfn ../float "$S/render/float"
TIME=$(python3 "$F/plate_times.py" "$V/plate/times.json")
echo "== presentation (slice $TIME, $PLA g)"
MARGARET_SLICE="{\"time\": \"$TIME\", \"grams\": $PLA}" MARGARET_WORK="$S/render" MARGARET_OUT="$V" MARGARET_DELIVER="$DL" \
    python3 presentation_v7.py > "$S/presentation.log" 2>&1
echo "== close-ups"; CLOSE_OUT="$F/diag7/$T" CLOSE_VIEWS=bow_q,stern_q,stern_aft,foredeck,anchor_q,anchor_side,anchor_front,cleat_bow17,cleat_spring,cleat_quarter,deck_cleats $B -b "$S/Margaret.blend" -P closeups.py > "$S/close.log" 2>&1
CLOSE_OUT="$F/diag7/$T" CLOSE_VIEWS=gooseneck CLOSE_HIDE=Preview_PaperSail $B -b "$S/Margaret.blend" -P closeups.py >> "$S/close.log" 2>&1
echo "CHAIN OK $T"
