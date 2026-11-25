# Margaret — 200 mm free-sailing yacht (v7g)

A printable model in the style of a **Jeanneau Sun Odyssey 43**: a likeness, not a copy. She has a blue underwater hull, white topsides and deck, a navy boot stripe and trim, and caulked teak on the cockpit, side decks and foredeck. **Margaret** is on both bows and repeated on the port transom face, and a navy delta anchor sits stowed on the bow roller as a separate-looking fitting.

The model prints as **one Bambu P2S plate in four colours**. It has a detachable, fillable ballast bulb, a keyed mast with a **printed navy shroud frame** (no thread stays), a printed furled genoa for display, and three interchangeable paper mainsails carrying the sail number **MGT 43**. A separate swan-neck table stand prints in one colour, with no pins into the model, and an optional printed display mainsail carries the same markings.

![Design views](Margaret-views.png)

![Afloat — calculated equilibrium](Margaret-afloat.png)

![How the paper sail is rigged](Margaret-sail-rigging.png)

![Display stand](Margaret-stand.png)

| File | Use |
| --- | --- |
| `Margaret-P2S.3mf` | Bambu Studio **project, already sliced**: one plate, 10 parts, 19 colour volumes. |
| `Margaret-paper-sails.pdf` | 1:1 templates: **start / medium / full** mainsails with the MGT 43 markings, an optional furled-genoa strip, rigging and trim notes. |
| `Margaret-afloat.png` | The exported model floated at its calculated waterline, upright and at 15° heel. |
| `Margaret-sail-rigging.png` | Where the paper sail is tied: head, luff, tack, clew and mainsheet. |
| `Margaret-stand.png` | The swan-neck stand: boat on the stand with the printed display sail, the fork close-up, the stand alone and the port profile, with print settings. |
| `Margaret-stand.3mf` | Bambu Studio project for the stand, **already sliced**: one navy part, no supports. |
| `Margaret-display-sail.3mf` | Optional printed display mainsail, **already sliced**: white with navy markings, laid flat, three peel-off mouse ears. Display only. |
| `Margaret.blend` | Editable assembled model (1 unit = 1 mm). Collections for each print group and for the paper-sail preview, plus seven cameras. The display stand and the printed display sail each have their own collection (the display sail is hidden in renders by default). |
| `views/` | Six renders: bow quarter, both profiles, cockpit, deck plan, exploded bulb with lead. `views/details/` has close-ups of the anchor, bow, foredeck and stern name, plus `name-depth-coupons.png` (why the name is 0.8 mm deep) and `name-gcode-check.png` (both names as the printer will lay them down). `views/afloat/` shows her at the calculated waterline, and `views/stand/` the stand renders plus both faces of the printed display sail with its markings. |
| `stl/` | Every printable colour body, in **assembled position** (not print orientation), including `Shrouds`, `Furler`/`Furler_ink`, `Stand` and `Display_sail`/`Display_sail_ink`, all in the same coordinates as the boat. |
| `data/` | `stats.json` (dimensions, rig, furler, anchor, sails), `stability.json` (sails, heel, CLR/CE), `hydro_check.json` (float, trim, righting curve), `mass.json` (sliced mass per part), `checks.json` (clearances and fits), `float.json`, `stand.json` (stand size, clearances, lift-off path, tipping angles), `display_sail.json` (size, mass, markings), `namecheck.json` and `transom_gates.json` (G-code proof that both names print legibly). |
| `scripts/` | Reproducible pipeline. `build_v7.py` builds the model (Blender 5.2, `MARGARET_OUT=<dir>`). The other scripts check, plate, slice-prep, compute hydrostatics, render and make the sheets/PDF; `stand_neck.py`, `display_sail.py` and `sail_marks.py` make the stand, the display sail and the shared sail markings. `scripts/coupon/` holds the name-printing experiment and the G-code name gates. |
| `REVIEW.md` | Full multi-model challenge/defend log (Steps 0–10) with each accept/defend decision. |

## Dimensions and proportions

| | Margaret | Real SO43 at 1:66 | Notes |
| --- | ---: | ---: | --- |
| Length overall | **200.0 mm** | 200 mm | 13.21 m ÷ 66.05 |
| Hull length | 197.5 mm | 194.4 mm | Plumb bow, raked open transom |
| Beam | 63.4 mm | 63.4 mm | |
| Waterline length | ≈ 180 mm | 173 mm | Slightly fuller ends for buoyancy |
| Freeboard (midships) | ≈ 15.6 mm | | |
| Draft | 55.5 mm | 30.3 mm | **Deliberately 1.8× deeper** so a model this small stands up to a breeze |
| Masthead above waterline | 240 mm | ≈ 257 mm | One-piece mast, limited by the 256 mm bed |
| Mast position | ≈ 37 % of LOA from the bow | similar | |
| Mainsail (paper) | 26 / 32 / 66 cm² | | Start / medium / full |

The above-water shape (sheer, coachroof, deck plan, open stern) follows the SO43 proportions. The keel and rig are changed on purpose: a scale keel and full-height rig would capsize a 64 g model in the lightest breeze.

## Will she float? (calculated from the exported STLs and the sliced masses)

| Item | Value |
| --- | ---: |
| Printed parts on board (per-object G-code mass; the display furler stays ashore) | 46.4 g |
| Paper sail, ties, seam glue, bulb glue | 1.8 g |
| Lead: **98 × 3 mm balls** | 15.7 g |
| **All-up mass** | **63.9 g** |
| Displacement at the design waterline (boot stripe) | 63.9 g |
| Hull sits deeper than designed / trim, lead poured **level** | 0.02 mm / 0.1° bow-down (bow 0.2 mm) |
| Metacentric height GM | 18.7 mm |
| Righting arm at 10° / 20° / 30° | 3.2 / 6.0 / 8.2 mm |
| Sealed hull self-rights up to (water in the cockpit past 131° is not modelled) | 140° |
| Deck edge reaches the water at | 31° |
| Water reaches the cockpit at | 131° |
| Extra lift if pushed fully under (sealed hull) | 165 g |
| Bulb capacity | ≈ 129 balls simulated ball-by-ball (98 needed) |

The bulb is placed so that lead poured in level trims her flat. The fin joins the front third of the bulb, as on real bulb keels. The printed shroud frame (0.5 g) sits higher than the old thread stays: compared with v7f, GM fell from 19.1 to 18.7 mm, the righting arm at 30° from 8.4 to 8.2 mm, and the bulb needs two fewer balls.

**These are predictions, not test results.** The physical check is simple: weigh the dry, rigged boat (without the furler), then add lead until boat + lead = **64 g**. She should float with the water just under the blue/white line.

## Printing

- **Settings:** Bambu Lab P2S, 0.4 mm nozzle, Bambu PLA Basic, **Textured PEI plate**. 0.16 mm layers, 2 walls, 7 % infill, supports from the build plate only, prime tower.
- **AMS mapping:** 1 white `#F6F5EE`, 2 blue `#15499D`, 3 navy `#173347`, 4 teak/tan `#BF8A54`.
- **Sliced result:** 13 h 06 min model time, 13 h 13 min total (235 layers), 209.0 g filament in total: white 80.7, blue 43.4, navy 55.9 (mostly purge), teak 29.0 g. About 320 colour changes; nothing outside the bed.
- **Mass of the printed parts:** **47.0 g** summed from the G-code per object (excluding supports and purge): 46.4 g goes sailing, plus the 0.6 g display furler.
- **Orientation, as laid out on the plate:**
  - Both hull halves print seam-face down. Supports inside them come out through the open seam.
  - The ballast cup prints opening up.
  - The fin with its bulb cap prints split face down.
  - The mast and its navy shroud frame print as one part, flat on the mast's aft face.
  - The furler prints flat on its flat face. The boom, rudder and wheels print flat.
- Don't scale or re-orient parts. The joints are sized for this slice.

## Assembly

1. **Clean up.** Remove the supports inside both hull halves. Clear the holes with a fine pin: the mast and boom holes, the sheet eye, the 4 hull lug holes and the 2 bulb post holes. Check that the two chainplate pockets and the stemhead pocket are clear.
2. **Hull.**
   - The lower blue hull and the white upper hull join at a seam **2.5 mm above the waterline**.
   - Push 6.5 mm lengths of 2 mm rod into the 4 lug holes; 1.75 mm filament plus glue also works.
   - Dry-fit, then bond the whole seam with slow epoxy. This seam must be **watertight**.
   - Float the empty hull for 10 minutes and check for seepage.
3. **Fin.** Glue the fin tenon into the socket under the hull (0.2 mm clearance per side). The fin is part of the top half of the bulb, so there is no gap between keel and bulb.
4. **Rudder.** The Ø2 mm stock pushes up into its Ø2.1 bore. Friction holds the trim, and the slotted navy cap on deck lets you turn it.
5. **Wheels.** Push each wheel's stub axle into the teardrop bore on its binnacle and fix it with a drop of CA. The rim faces aft, toward the helm seat.
6. **Mast and shroud frame.**
   - Lower the mast straight down: the D-shaped heel keys into the blind deck socket while the two shroud-frame foot tabs drop into the chainplate pockets beside the coachroof (0.2 mm clearance per side).
   - The heel bottoms in its socket and carries the weight; the tabs stop 0.5 mm above the pocket floors and only brace the mast sideways. No glue is needed, so the mast lifts out for transport. A drop of CA in each pocket makes it permanent.
7. **Boom.** Tie a thread loop through the boom's forward hole and round the mast, so the boom sits on the gooseneck saddle at 43 mm and swings freely (checked clear through ±45°).
8. **Furled genoa (display only).** Drop the navy foot tab into the stemhead pocket on the bow, then hang the hook over the masthead cap (0.36 mm clearance). Lift it off before sailing.

## Stern and decks

- **Open stern:** the cockpit sole steps down to a full-width teak bathing platform, set into a reverse-raked transom (~8°). The folding swim ladder lies stowed fore-aft on the platform, in navy relief.
- **Teak:** cockpit sole and seats, side decks and foredeck. Planks spring parallel to the deck edge and are **nibbed** square into the king plank and coachroof margins at the bow, as on real teak decks.

## Bow anchor and transom name

- **Anchor:** a navy delta anchor lies stowed on the bow roller, and reads as a separate fitting although it prints as part of the white upper hull (nothing to glue):
  - its 1.0 mm shank runs over the roller between the cheeks with 0.65 mm of daylight each side and 0.9 mm of air under it;
  - it rests only on the roller and, through a D-ring shackle, on a small white deck chock;
  - the fluke hangs ahead of the stem with a 0.75 mm shadow gap and touches it only at its toe, which is where its print starts. The crown stands about 1.5 mm proud of the cheeks.
  - It stays inside the 200 mm length and adds no supports.
- **Name on the stern:** **Margaret** is inlaid 0.8 mm into the port transom face, beside the walk-through to the bathing platform, and reads left to right from astern. It matches the bow names (navy, bold).
- A small white pad inside the transom keeps 0.85 mm of white behind the letters. Shallower inlays (0.4 and 0.6 mm) looked fine in Blender but sliced into broken navy fragments; test coupons showed 0.8 mm is the depth at which the slicer prints every stroke. The real plate's G-code was checked letter by letter: every stroke of every letter prints on every layer (`data/transom_gates.json`).

## Rig and sails: display or sailing

**In short:** the whole rig is printed and needs no thread stays. The mast stands in its keyed blind socket. A flat navy **shroud frame**, printed in one piece with the mast, carries the cap shrouds from the hounds over both spreader tips to chainplates beside the coachroof, plus the lower shrouds. There is no backstay: a printed split backstay does not fit on the plate, and the masthead is too thin for a clip, so the rig carries only what can be printed. The forestay is suggested by the printed **furled genoa**. The paper sail weighs about 0.5 g, so she floats on her line and sails; the printed display sail weighs 4.5 g, so it is for the shelf.

| Purpose | Rig | Sail |
| --- | --- | --- |
| **Sailing** | Printed mast + shroud frame, boom; furler **off** | Paper (start / medium / full), 0.5–0.7 g |
| **Display** | The same, plus the printed furled genoa | Paper full sail, or the **printed display sail** (`Margaret-display-sail.3mf`) |

- **Scale honesty:** the shroud strips are 1.0 × 0.6 mm, about 66 mm thick at full size, which is what a 0.4 mm nozzle prints reliably. They read as rigging in navy, and they brace the mast sideways without any tensioning.
- **Furler:** a 226 mm white furled genoa on a navy drum, with a D-shaped section 2.2 mm wide. Its foot tab sits in the stemhead pocket (0.2 mm clearance) and the hook hangs over the masthead cap.

**Sail markings (paper and printed):**
- The sail number is **MGT 43** (code over number), in 6.8 mm capitals: the racing-rules minimum of 450 mm for a boat over 11 m, at 1:66. Two navy waves near the head are Margaret's insignia. Two reef rows show cringle patches and reef points.
- As on a real mainsail, each side carries its own set: the **port** set is lower and reads normally from port; the **starboard** set is higher and reads correctly from starboard. On the paper template the starboard set is printed mirrored, so it reads through the taped sheet.
- The marked paper main is shown in `Margaret-views.png`. To use another code or number, set `SAIL_CODE` / `SAIL_NO` before running `display_sail.py` and `presentation_v7.py`.

**Printed display sail (optional):**
- The same outline and holes as the FULL paper sail: 0.52 mm white PLA with seven cross-cut seams, four battens, raised tabling and corner patches on the starboard face.
- **Markings in navy:** the port number is inlaid into the first layer (crisp on the bed face); the starboard number is a 0.16 mm relief on a seam-free panel (seams stop 0.6 mm short of the numbers); the wave insignia goes through the full thickness.
- 66.9 cm², 4.5 g. About 20 min to print (27 min with heating and calibration); 6.8 g white and 0.8 g navy filament including purge.
- Print flat as sliced, no supports. Let the plate cool before peeling it off, then peel or snip off the three Ø10 mm mouse ears at the head, tack and clew (they only stop the corners lifting).
- Tie it on exactly like the paper full sail (same holes, same thread).
- **Don't sail with it.** It is about 8× the paper sail's weight, high up: it raises her centre of gravity by about 7 mm and cuts the metacentric height from 19 to about 12 mm. She still floats upright, but heels much more. Swap to paper before she goes in the water.
- If the starboard number prints faint on your printer, rebuild with a 0.24 mm relief (`display_sail.py`, one more layer).

## Paper sails

Print the PDF at **100 %** and check the 50 mm bar. Use 80–100 g/m² paper. The grey lines inside each outline are cloth detail (seams, battens, tabling, corner patches, reef rows); the navy marks are the sail number and insignia. Cut on the black line; the labels stay on the waste paper below the foot. Laminate both faces with **matte** clear tape (it waterproofs the sail and keeps the grey seams visible without shine), then pierce the marked holes. The full sail weighs ≈ 0.5–0.7 g with tape and is already in the 64 g budget.

1. **Head:** tie the reinforced head hole to the masthead hole (full sail), or round the mast just above the upper spreader (start and medium).
2. **Luff:** a small thread loop through each luff hole and round the mast, every 20 mm. Keep them off the spreader roots (dashed marks).
3. **Tack:** lash the tack hole round the mast just above the boom.
4. **Clew:** tie it down to the matching boom hole. Counting from the aft end of the boom: full 1st (70 mm aft of the mast), medium 2nd (58 mm), start 3rd (46 mm).
5. **Mainsheet:** from the 4th boom hole down to the eye on the coachroof below it. Tie it so the boom sits about 15° off the centreline to start.

| Sail | Area | Heel at 1 m/s | Heel at 1.5 m/s | Heel at 2 m/s | Use |
| --- | ---: | ---: | ---: | ---: | --- |
| **Start** | 26 cm² | 1° | 2° | 4° | First trials, normal light breeze |
| Medium | 32 cm² | 1° | 3° | 5° | Steady light air |
| Full | 66 cm² | 3° | 7° | 12° | **Only below ≈ 1.5 m/s**, or display |

The sail's centre of effort is slightly ahead of the keel's centre of lateral resistance (4 mm with the full sail, 12 mm with the start sail), so she may bear away. Turn the rudder's trailing edge a few degrees to windward and ease the sheet until she sails straight.

## Ballast (detachable bulb, 3 mm lead balls)

The bulb splits at a horizontal glue plane. The **upper half (fin cap)** is part of the fin. The **lower half (cup)** is a hollow shell with 0.9 mm walls. Two Ø2 mm posts in the cup locate it in Ø2.4 mm holes in the cap. They stop it rotating, but they do not hold it on.

1. **Weigh** the finished, rigged boat without lead and without the furler. Lead target = **64 g − that mass** (≈ 15.7 g ≈ 98 balls at 0.16 g each).
2. **Pour the lead in level** (the cup standing upright) and press the cup onto the cap. **Tape the seam all round with waterproof tape** for trials; the bulb stays fully detachable.
3. **Float it in a tank.** The water should sit just under the blue/white line, level fore and aft. Check that she rights herself from a gentle heel to both sides.
4. **Sail on a retrieval line**, start sail first.
5. **Close the bulb for good.**
   - Lock the balls with a little thin epoxy (counted in the 0.4 g bulb-glue allowance).
   - Glue the cup to the cap with epoxy on the full rim.
   - Repeat the float test.

**Lead safety:** use intact balls; never cut, sand or heat lead. Keep it away from children and pets, wash your hands after handling, and seal it fully in epoxy.

## Display stand (separate print)

A swan-neck stand, like a model-aircraft stand: a thin oval base and **one** curved neck that leans forward and ends in a small fork under the hull. Nothing enters the model: no pins, no glue. Three reviewers on different models designed and then challenged it (see `REVIEW.md`, Step 10).

- **Size:** 74 × 60 × 48 mm overall; a 73.5 × 60 × 1.8 mm oval base with a bevelled top edge and one neck (6.0 × 5.2 mm at the root, 2.5 mm root fillet) leaning 45° up to the fork.
- **How it holds her:**
  - The fork's two pads, 18 mm long, follow the hull bottom either side of the keel with zero gap, and carry her weight.
  - The keel root sits in the fork slot with 0.4 mm per side, so she cannot roll.
  - The fork's closed front stops her going forward.
  - A low saddle under the bulb tail (0.4 mm clear, 1.6–3.0 mm high over the bulb flat) stops her sliding aft. The neck stays 2.2 mm clear of the bulb nose.
- **On and off:** lift her 4 mm, slide her 32 mm aft, then lift her away; put her on in reverse. A check of 615,839 vertex positions along that path found no contact.
- **Calculated, not yet measured** (full lead / no lead / printed display sail): her centre of gravity is 5.3 / 7.1 / 5.4 mm inside the aft end of the pads. The whole assembly tips sideways at 32° / 27° / 29° and forward at 36° / 29° / 32°. Check these on a tilted board after printing.
- **Print:** open `Margaret-stand.3mf` and print as sliced. One piece, upright, navy PLA, 15 % infill, 3 walls, no supports (steepest overhang 48°, limit 50°). 29 min 28 s (36 min 30 s with heating and calibration), 10.1 g.
- **Use:** fit the bulb (taped or glued) before putting her on; the saddle locks the bulb tail. Optional felt pads under the base protect the table.
- **Rig and tune the sail off the stand.** Don't tie the sail or fit the furler while she sits on it.
- The fork cheeks hide the top of the fin. Cutting them back to show the fin's leading edge would need a 65° overhang (supports on a 1.8 mm part), so the reviewers kept them.

## Rebuilding (optional)

All scripts are in `scripts/` and expect Blender 5.2 and Bambu Studio on macOS. Run them in this order:

1. `MARGARET_OUT=build blender -b --factory-startup -P build_v7.py` (generator; needs `hullgen.py` and `hull_params_v7.json` beside it).
2. `MARGARET_OUT=build blender -b --factory-startup -P check_v7.py` (fits: rudder, wheels, shroud feet, furler hook and tab, cup/cap), then `plate_v7.py` the same way.
3. In `build/plate`: `MARGARET_WORK=$PWD python3 prepare_slice.py`, slice with Bambu Studio's CLI, then `gcode_mass.py` on the G-code to get `mass.json`.
4. `SLICE_MASS=build/plate/mass.json MARGARET_OUT=build python3 hydro_check.py` (float, trim, righting curve), and `stability_v7.py` in Blender with the same variables (sails, heel, CE/CLR).
5. Display sail (before the renders, which use its markings on the paper-sail preview): `MARGARET_OUT=build SAIL_OUT=build/dsail blender -b --factory-startup -P display_sail.py`, then `./stand_slice.sh <abs path to build/dsail> Display_sail-bed.stl Margaret-display-sail.3mf 1 "Margaret display sail"`. `SAIL_DIR=… SAIL_IMG=… blender -b --factory-startup -P sail_show.py` renders both faces.
6. `present_v7.py`, `float_v7.py`, `closeups.py` (renders), then `presentation_v7.py` (sheets and PDF).
7. Stand: `MARGARET_OUT=build STAND_OUT=build/stand DISPLAY_SAIL_JSON=build/dsail/display_sail.json blender -b --factory-startup -P stand_neck.py` (the build stops if any clearance, lift-off or overhang check fails), then `./stand_slice.sh <abs path to build/stand>`, and run `stand_neck.py` once more so it uses the sliced mass. Then `STAND_DIR=… SAIL_DIR=… blender -b Margaret.blend -P stand_show.py` adds the stand and display sail to the blend and renders them; run `presentation_v7.py` again for the stand sheet.
8. Name gates on the sliced plate: `python3 coupon/transom_gates.py build` (must print PASS) and `python3 coupon/namecheck.py build preview.png`.

`run_chain.sh <tag>` runs everything from `plate_v7.py` in step 2 through step 6, after the build and check (paths at the top of the script point to the author's machine). The earlier raked-wall stand generator (`stand_v7.py`) is in the git history (commit `6378dd0`).

## Status

The design has been modelled and checked digitally:
- all parts are manifold, with no tiny colour islands
- clearance and swing checks pass, with **0 mm³** overlap between the cup and the cap; the furler hook clears the masthead by 0.36 mm and the shroud feet clear their pockets by 0.21 mm
- the plate has been sliced, and the per-part G-code mass was fed back into the float calculation
- the G-code was checked layer by layer to prove both names print legibly
- buoyancy, trim and the righting curve were computed independently from the exported STLs
- the stand's on/off path, clearances, overhangs and tipping angles were computed from the same geometry
- all of the above was challenged by several independent model reviewers (see `REVIEW.md`).

**It has not yet been printed, leak-tested or sailed.** The ball count, trim, heel, fit and tipping figures are calculations. Confirm them in the tank and on a test print before gluing the bulb shut.
