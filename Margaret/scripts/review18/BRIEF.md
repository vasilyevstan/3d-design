# Review 18 — the furled genoa does not hold at the masthead (Margaret, 200 mm printed yacht, Bambu P2S, PLA, 0.4 nozzle)

## User report
"how is head sail connected to the main mast? glue? does not seem to fit" -> "no, the head sail and the mast do not hook,
maybe glued" -> "okay it hooks into the sail, but not to the mast and then it will be wobbly".

## Current design (v7n, identical since v7m)
- Display-only furled genoa ("furler"): 226.1 mm white D-section body on the forestay axis, 16.0 deg from vertical
  (axis unit, stemhead -> masthead = (-0.276, 0.961) in x (fwd +) / z (up +)). Prints flat on its y = -0.6 face.
- Foot: navy drum + foot tab 1.1 x 1.1 mm, 3.4 mm long along the axis, in a stemhead pocket in the deck
  (1.5 x 1.5 mm, 4.0 mm deep along the axis, 0.2 mm/side). Tab engagement 2.4 mm, tab bottom 1.6 mm above the pocket floor.
  The tab allows about +-4.7 deg tilt, i.e. the head can swing ~ +-18 mm sideways if nothing holds it.
- Head: an inverted-U hook (1.5 x 2.0 mm stock) over the masthead cap. The hook is a prism along y (open tunnel,
  y -0.6..1.4) with 0.38-0.42 mm clearance over the crown and both legs; aft leg 1.2 mm deep. The furler hangs on
  its crown; the foot tab only locates the foot.
- Masthead cap (part of the one-piece mast, mast prints lying on its flat aft face): 2.65 mm fore-aft x 2.4 mm wide
  x 5.6 mm tall (z 235.0..240.6). A 0.84 mm fore-aft "masthead hole" at z 237.8 is used to tie the paper mainsail's head.

## Measured (STL section script, review18/hook_path.py)
- Parked, mast home: hook clears cap 0.38 / 0.42 / 0.40 mm; no overlap.
- Nothing retains the hook sideways: it is a tunnel open at both y ends, so the head slides off / wobbles.
- Assembly along the stay (hook on first, then push the tab 2.4 mm down) collides; only a sideways slide works.
- Mast standing high by e: fits for e <= 1.5 mm, NO pose fits for e >= 2.0 mm. The user's earlier v7m print had a
  slicer support column in the blind mast socket that held the mast ~5.8 mm high (fixed in v7n plates; README tells
  old prints to drill it out). So on the user's boat the hook very likely could not reach at all.

## Proposal v7o (hull plates unchanged — the 7 h upper-hull print stays; only plate 3, 51 min, is reprinted)
Keyed masthead tang, like a forestay tang in a masthead crane:
1. Mast cap widened 2.4 -> 3.2 mm (y +-1.6), same 2.65 mm depth and height. A slot cut into it, open to the FRONT and
   the TOP: y -0.8..0.6 (1.4 mm), from 0.9 mm forward of the aft face to the front, 2.8 mm deep from the cap top.
   Slot side walls 0.8 / 1.0 mm. In print (mast on its aft face) the slot is an upward-open groove: no supports.
2. The masthead hole moves down 1.4 mm (z 236.4) to stay under the slot floor (0.98 mm of material between).
3. Furler hook removed. A flat tang 1.0 mm thick (y -0.6..0.4, on the print bed face) grows aft from the furler head
   into the slot: 0.2 mm clearance each side, 0.2 mm off the aft wall and 0.2 mm above the slot floor in the design
   pose, top 0.4 mm proud of the cap. Engagement 1.55 mm fore-aft x 2.6 mm deep.
4. Load path: gravity rotates the leaning furler aft about its foot and slides it down the stay, so the tang sits on
   the slot floor and against the aft wall; the slot walls hold it sideways (head play ~0.2 mm instead of +-18 mm).
5. Foot tab lengthened 1 mm (3.4 mm engagement, bottom 0.6 mm above the pocket floor; 0.3 mm with the mast heel on its
   socket floor). The furler then still seats if the mast stands up to ~2.4 mm high (was 1.5 mm).
6. Fitting: foot tab into the stemhead pocket, lower the head so the tang drops into the slot from above (moving down
   the stay carries it forward, gravity swings it back onto the aft wall). Removal: lift the head a little forward and up.
   No glue needed; a drop of glue in the slot makes it permanent for a shelf model (but the furler is meant to come off
   for sailing).

## Rejected alternatives
- Glue only: permanent; the mast goes in vertically while the tab goes in along the 16 deg axis, so a glued furler
  binds the mast; and the furler is meant to stay ashore when sailing.
- Closed cup over the cap: must go on vertically, the foot pocket is along the axis (16 deg conflict).
- Fork on the furler straddling the cap: needs a tine below the furler's print-bed face.
- Pin across the masthead (y): slides off sideways like the hook.
- Thread lashing: fiddly at this scale; keep as a stop-gap for the existing print.

## Questions
1. Will this hold firmly and stop the wobble? Any failure mode (tang levering out, slot walls splitting, tang too thin)?
2. Printability of a 1.4 mm slot with 0.8/1.0 mm walls in a mast printed on its aft face, and of a 1.0 mm tang printed flat.
3. Is 0.2 mm per side right for a sideways slot fit on a P2S in PLA (tang in the bed plane, slot walls as perimeters)?
4. Fitting and removal sequence: realistic by hand? Better sequence?
5. Is there a SIMPLER robust option we missed? Do NOT propose extra machinery.
6. Looks: a 3.2 mm masthead box with a tang — acceptable at 1:66?
Answer with: verdict (adopt / adopt with changes / reject), the concrete changes with numbers, and anything to verify.
