# Margaret — 200 mm free-sailing yacht (v7o)

A printable model in the style of a **Jeanneau Sun Odyssey 43**: a likeness, not a copy. She has a blue underwater hull, white topsides and deck, a navy boot stripe and trim, and caulked teak on the cockpit, side decks and foredeck. **Margaret** is on both bows and repeated on the port transom face, and a navy delta anchor sits stowed on the bow roller as a separate-looking fitting. Six **navy horn cleats** stand just inside the toe rail where the real boat has them: a bow pair, a spring pair at the widest point and a pair on the stern quarters. There are no railings: at 1:66 a stanchion would be 0.4 mm and a lifeline 0.1 mm, finer than a 0.4 mm nozzle can print.

Everything prints from **one Bambu Studio project with four P2S plates** in four colours (see [Printing](#printing)). The model has:
- a detachable, fillable ballast bulb;
- a keyed mast with a **printed navy shroud frame** whose chainplates sit **near the deck edge**, as on the real boat (no thread stays);
- a printed furled genoa for display, keyed into a slot in the masthead so it sits firm;
- three interchangeable paper mainsails carrying the sail number **MGT 43**.

A swan-neck table stand (plate 4, navy) **rises from aft, between the rudder and the keel**, and lifts her up by the hull without any pins. An optional printed display mainsail on the same plate carries the same markings.

![Design views](Margaret-views.png)

![Afloat — calculated equilibrium](Margaret-afloat.png)

![How the paper sail is rigged](Margaret-sail-rigging.png)

![Display stand](Margaret-stand.png)

| File | Use |
| --- | --- |
| `Margaret-P2S.3mf` | Bambu Studio **project, already sliced**: every printable part on **four plates** — 1 upper hull; 2 lower hull, fin, ballast cup and rudder; 3 mast, boom, furler and wheels; 4 display stand and display sail. Objects are named and carry their own filament. |
| `Margaret-paper-sails.pdf` | 1:1 templates: **start / medium / full** mainsails with the MGT 43 markings, an optional furled-genoa strip, rigging and trim notes. |
| `Margaret-afloat.png` | The exported model floated at its calculated waterline, upright and at 15° heel. |
| `Margaret-sail-rigging.png` | Where the paper sail is tied: head, luff, tack, clew and mainsheet. |
| `Margaret-stand.png` | The swan-neck stand rising from aft: boat on the stand with the printed display sail, the fork under the hull, the stand alone and the port profile, with print settings. |
| `Margaret.blend` | Editable assembled model (1 unit = 1 mm). Collections for each print group and for the paper-sail preview, plus seven cameras. The display stand and the printed display sail each have their own collection (the display sail is hidden in renders by default). |
| `views/` | Six renders: bow quarter, both profiles, cockpit, deck plan, exploded bulb with lead. `views/details/` has close-ups of the anchor, bow, foredeck, stern name, deck edge (`deck-edge`), cleats (`deck-cleats`, `cleat-bow`, `cleat-spring`, `cleat-quarter`), the boom lashing (`gooseneck`), chainplate and rig, plus `name-depth-coupons.png` (why the name is 0.8 mm deep) and `name-gcode-check.png` (both names as the printer will lay them down). `views/afloat/` shows her at the calculated waterline, and `views/stand/` the stand renders plus both faces of the printed display sail with its markings. |
| `stl/` | Every printable colour body, in **assembled position** (not print orientation), including `Shrouds`, `Furler`/`Furler_ink`, `Stand` and `Display_sail`/`Display_sail_ink`, all in the same coordinates as the boat. |
| `data/` | `stats.json` (dimensions, rig, furler, anchor, sails), `stability.json` (sails, heel, CLR/CE), `hydro_check.json` (float, trim, righting curve), `mass.json` (sliced mass per part), `times.json` (time and filament per plate), `checks.json` (clearances and fits), `fits_gcode_v7o.json` and `mast_fit_v7o.txt` (joints as printed), `tang_fit.json` (furler head in the masthead slot: gaps, fitting path, lift to release) and `slot_gcode.json` (the slot, lip and tang as sliced), `support_probe.json` (what the slicer puts inside the mast bore), `column_compat.json` (v7m/v7n lower hull compatibility), `probe17.json` (mast seating gauge, rudder tube wall), `float.json`, `stand.json` (stand size, clearances, lift-off path, forward hold, tipping angles), `stand_strength.json` (neck stress on every print layer, safety factors, sag), `display_sail.json` (size, mass, markings), `namecheck.json` and `transom_gates.json` (G-code proof that both names print legibly). |
| `scripts/` | Reproducible pipeline. `build_v7.py` builds the model (Blender 5.2, `MARGARET_OUT=<dir>`). The other scripts check, plate, slice-prep, compute hydrostatics, render and make the sheets/PDF; `stand_neck.py`, `stand_strength.py`, `display_sail.py` and `sail_marks.py` make and check the stand, the display sail and the shared sail markings. `scripts/coupon/` holds the name-printing experiment and the G-code name gates; `scripts/review14/` and `scripts/review17/` the joint, mast-bore and compatibility checks. |
| `REVIEW.md` | Full multi-model challenge/defend log (Steps 0–17) with each accept/defend decision. |

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
| Full mainsail luff | 188 mm | 231 mm (P = 15.26 m) | 81 %: the mast stops short of full height (bed limit) and the boom sits higher above the deck |

The above-water shape (sheer, coachroof, deck plan, open stern) follows the SO43 proportions. The keel and rig are changed on purpose: a scale keel and full-height rig would capsize a 64 g model in the lightest breeze.

## Will she float? (calculated from the exported STLs and the sliced masses)

| Item | Value |
| --- | ---: |
| Printed parts on board (per-object G-code mass; the display furler stays ashore) | 50.1 g |
| Paper sail, ties, seam glue, bulb glue | 1.8 g |
| Lead: **75 × 3 mm balls** | 12.0 g |
| **All-up mass** | **63.9 g** |
| Displacement at the design waterline (boot stripe) | 63.9 g |
| Hull sits deeper than designed / trim, lead poured **level** | 0.02 mm / 0.08° bow-down (bow 0.15 mm) |
| Metacentric height GM | 16.0 mm |
| Righting arm at 10° / 20° / 30° | 2.7 / 5.0 / 6.8 mm |
| Sealed hull self-rights up to (water in the cockpit past 130° is not modelled) | 132° |
| Deck edge reaches the water at | 31° |
| Water reaches the cockpit at | 130° |
| Extra lift if pushed fully under (sealed hull) | 165 g |
| Bulb capacity | ≈ 127 balls simulated ball-by-ball (75 needed) |

The bulb is placed so that lead poured in level trims her flat. The fin joins the front third of the bulb, as on real bulb keels. v7j thickens the underwater hull from 0.85 to 1.2 mm (a test print of the blue half came out too thin). That adds 3.7 g of PLA, which replaces 23 balls of lead to keep the 64 g all-up mass; her centre of gravity rises 2.6 mm, so GM drops from 18.6 to 16.0 mm and the righting arm at 30° from 8.1 to 6.8 mm. She is still stiff for a light-air model: the full sail heels her 14° at 2 m/s instead of 12°. v7k only changes the joint clearances (see Assembly); it moves 0.07 g of PLA and one lead ball, and GM is 15.9 mm. v7l only opens the rudder bore to Ø2.5 (the printed Ø2.1 bore did not take the stock); mass, lead and float figures are unchanged. v7m only thickens the display furler, which stays ashore, so nothing here changes. v7n moves the cleats and opens the mast bore; it is re-sliced as four plates, and the per-object G-code gives 50.1 g of PLA on board, so the lead goes from 74 to 75 balls and GM is 16.0 mm. v7o only changes the masthead and the furler's head (plate 3): the mast gains 0.01 g and the furler stays ashore, so every float figure is unchanged.

**These are predictions, not test results.** The physical check is simple: weigh the dry, rigged boat (without the furler), then add lead until boat + lead = **63.9 g**. She should float with the water just under the blue/white line.

## Printing

- **Settings:** Bambu Lab P2S, 0.4 mm nozzle, Bambu PLA Basic, **Textured PEI plate**. 0.16 mm layers, 2 walls, 7 % infill, supports from the build plate only, prime tower.
- **Hull walls (v7j):** 1.2 mm below the waterline, rising smoothly to the 1.7 mm seam land; 0.85 mm topsides. The thickness is in the model, so no slicer change is needed: the G-code lays two wall lines with solid infill between them, and per layer it deposits 90–97 % of the cross-section area, so there are no gaps (`scripts/wall_fill.py`).
- **AMS mapping:** 1 white `#F6F5EE`, 2 blue `#15499D`, 3 navy `#173347`, 4 teak/tan `#BF8A54`.
- **Four plates, one project, all already sliced (v7o).** Plates 1–3 are the boat; plate 4 is the display stand and the optional printed display sail. In Bambu Studio, pick a plate and press *Print plate*. Times are as Bambu Studio shows them (with heating and calibration). The filament column is what leaves the spools, including colour-change purge, the prime tower and the supports inside the hull halves, so it is much more than the finished parts.

  | Plate | Parts | Time | Filament from the spools | Finished parts |
  | --- | --- | ---: | --- | ---: |
  | 1 | Upper hull: deck, coachroof, cleats, names, teak | 7 h 08 min | white 73.6 + navy 22.7 + teak 27.6 = 123.9 g | 25.8 g |
  | 2 | Lower hull, fin with bulb cap, ballast cup, rudder | 2 h 48 min | white 3.4 + blue 33.0 + navy 5.8 = 42.2 g | 21.4 g |
  | 3 | Mast with shroud frame, boom, furled genoa, two wheels | 0 h 51 min | white 11.5 + navy 3.5 = 15.0 g | 4.5 g |
  | 4 | Display stand, printed display sail | 1 h 12 min | white 7.2 + navy 13.3 = 20.5 g | 15.2 g |

  The boat (plates 1–3) takes **10 h 47 min** and 181 g of filament for **51.6 g** of parts. All four plates need about 96 g white, 33 g blue, 45 g navy and 28 g teak: load at least 100 / 40 / 50 / 35 g so a spool doesn't run out mid-plate.
- **Colours:** every object carries its own filament in the project, so the fin and the ballast cup are blue (in v7m they opened as white, because only their part, not the object, had the filament set). The per-object G-code confirms it: fin and cup 100 % blue, stand 100 % navy.
- **Mast bore:** support blockers sit over both halves of the mast bore. Without them the slicer filled the blind socket in the lower half with a support column, which stopped the mast going home (v7m). The G-code now leaves only one loose first-layer strand (about 22 mm) at the mouth of each half; pick it out (Assembly step 1).
- **Mass of the printed parts:** **50.1 g** goes sailing (summed from the G-code per object, excluding supports and purge), plus the 1.5 g display furler. The lower hull alone is 15.9 g.
- **Orientation, as laid out on the plates:**
  - Both hull halves print seam-face down. Supports inside them come out through the open seam.
  - The ballast cup prints opening up.
  - The fin with its bulb cap prints split face down.
  - The mast and its navy shroud frame print as one part, flat on the mast's aft face.
  - The furler prints flat on its flat face: 2.8 mm tall, 17 layers with a solid core, 1.9–2.7 mm on the bed along its whole length. When the plate has cooled, flex the plate and lift the furler from the drum end, not by the head tang. The mast's masthead slot prints as an open groove, with the lip as a 1.5 mm bridge; no supports. The boom, rudder and wheels print flat.
- Don't scale or re-orient parts. The joints are sized for this slice.
- **Upgrading a v7n print to v7o:** reprint **plate 3** only (51 min): the new mast and the furler with its keyed head. Every other part is byte-identical to v7n (STLs compared). Until then, an old furler stays on if you seat the mast fully and tie its hook to the masthead with one turn of thread.
- **Upgrading a v7m print:** reprint plate 3 and **plate 1** (upper hull: new cleat positions and the wider mast bore). Reprint the fin and cup (plate 2) only if yours came out white. The lower hull is unchanged outside the mast socket (checked every 0.1 mm across the whole part, `data/column_compat.json`), so a printed v7m lower mates with the new upper as long as the halves are **not yet glued**; clear its mast socket as in Assembly step 6. If they are already glued, keep the hull: clear the socket (step 6) and live with the v7m cleat positions, or reprint plates 1 and 2.
- **Older prints:** from v7l, the same as from v7m (the furler on plate 3 was too thin to print). From v7j or earlier, also reprint the lower hull (plate 2: 1.2 mm bottom, tighter fin socket, Ø2.5 rudder bore).

## Assembly

Joint clearances in v7o, measured on the sliced toolpaths (`data/fits_gcode_v7o.json`, `data/mast_fit_v7o.txt`, `data/slot_gcode.json`) and reviewed in `REVIEW.md` Steps 14–18. Small printed holes come out smaller than these toolpath figures (the v7j rudder failed this way), so the rudder now has real running clearance:

| Joint | Model | As printed (per side) | Purpose |
| --- | --- | --- | --- |
| Fin tenon in hull socket | 0.10 mm | 0.10 / 0.11 mm | epoxied; small enough to square by hand |
| Rudder stock in its bore (both halves) | 0.25 mm (Ø2.5 bore, Ø2.0 stock) | 0.18–0.24 mm on the toolpaths; ≈ 0.1–0.2 mm after the Ø2.4 drill pass | free running; PTFE tape on the stock holds trim |
| Mast heel in its D-socket (both halves) | 0.25 mm | 0.26 mm on every layer (bore 4.25 × 3.11 mm, heel 3.72 × 2.59 mm) | slides home by hand; no glue |
| Bulb posts in cap holes | 0.15 mm | ≈ 0.12 mm | locate the cup; tape or epoxy holds it |
| Wheel stubs in binnacle bores | 0.2 mm | 0.2 mm, 0.8 mm spare depth | CA glued |
| Furler head tang in the masthead slot | 0.25 mm each side; seated 0.18 down, 0.20 aft, 0.22 to the lip | slot 1.51 mm on every layer, tang 1.0 mm (6 layers): ≈ 0.25 mm each side | drops in from above; the lip holds it fore-aft; no glue |

![Joint cross-sections, v7j vs v7l](views/details/assembly-fits.png)

1. **Clean up.** Remove the supports inside both hull halves. Pick out the loose first-layer strand at the mouth of the mast bore in each half (on the seam face). Clear the holes with a fine pin: the boom holes, the sheet eye, the 4 hull lug holes and the 2 bulb post holes. Check that the two chainplate pockets and the stemhead pocket are clear.
2. **Hull.**
   - The lower blue hull and the white upper hull join at a seam **2.5 mm above the waterline**.
   - Push 6.5 mm lengths of 2 mm rod into the 4 lug holes (Ø2.15 mm, 3.5 mm deep in each half). 1.75 mm filament also works, but it has about 0.2 mm of play per side and will not line up the boot stripe by itself: align it by eye and tape or clamp the halves while the epoxy cures. The pins only line the halves up.
   - Sand off any elephant foot on both seam faces so the halves close flush at the boot stripe.
   - **Use the 2 mm rod pins**, not filament, for the glue-up: the rudder bore runs through both halves, and filament pins allow a 0.2 mm step at the seam that eats the rudder's clearance.
   - Dry-fit all four pins, then bond the whole seam with slow epoxy. The epoxy on the 1.7 mm-wide seam land is what holds the halves together and seals them. This seam must be **watertight**.
   - Glue the ring of seam land round the rudder tube too: it is the seal between the flooded rudder tube and the inside of the hull. The tube wall is thinnest there (0.45 mm, just below the waterline), so don't skip this ring.
   - **After the epoxy cures, true the rudder bore:** twist a **Ø2.4 mm drill bit by hand** (pin vise or fingers, no power drill) down through the bore from the deck in one pass. It clears any seam step, squeeze-out and blobs. On halves printed before v7l (Ø2.1 bore) the same pass opens the bore and leaves a 0.73 mm wall; do not use Ø2.5 on those.
   - The v7o (= v7n) upper half mates with an already-printed v7l or v7m lower half that is not yet glued: the seam faces, lugs and the whole lower hull are identical outside the mast socket (ray-cast every 0.1 mm, `data/column_compat.json`).
   - **Bubble test (required before any lead goes in):** hold the glued, empty hull completely under water for a minute. A stream of bubbles marks a leak: dry it, epoxy the spot (usually the seam or the rudder-tube ring) and test again.
3. **Fin.** The socket is **0.1 mm per side** larger than the tenon (v7j had 0.2 mm, which let the fin rock ±4.8°; now about ±2.4° before glue). Dry-fit first. Then turn the hull upside down on its seam face, fill the socket with slow epoxy, push the tenon in, square the fin to the hull with a set square, and tape it until cured; the epoxy fills the gap and fixes the angle. The fin is part of the top half of the bulb, so there is no gap between keel and bulb.
4. **Rudder.** First push the bare rudder up from below: the Ø2 mm stock must turn freely in its bore. If it binds, scrape the thin ridge along the side of the stock that printed on the bed. Then wind **1–2 turns of PTFE plumber's tape** round the stock in a 2 mm band starting 0.5 mm below its top (the slotted tip sits in the deck counterbore and touches nothing). Push it back in and add or remove a turn until it turns with firm finger pressure, holds its angle and does not drop out. The slotted navy tip on deck lets you set the trim. Don't use paper masking tape: it goes soft in the wet tube and seizes.
5. **Wheels.** Push each wheel's Ø1.6 mm stub axle into the teardrop bore (Ø2.0, 0.2 mm per side) on its binnacle and fix it with a drop of CA. The bore is about 0.8 mm deeper than the stub. The rim faces aft, toward the helm seat.
6. **Mast and shroud frame.**
   - Lower the mast straight down: the D-shaped heel keys into the blind socket (through the deck into the lower half) while the two shroud-frame foot tabs drop into the chainplate pockets near the deck edge (0.2 mm clearance per side).
   - **Fully home**, the shroud-frame feet rest on the chainplate blocks, the tabs hang 0.2 mm above the pocket floors and the heel stops 0–0.3 mm above the socket floor. Check it with a ruler: from the top of the deck collar round the mast to the top of the gooseneck saddle (the small collar where the boom is lashed) it reads **19.5 mm** (up to 19.8 mm is fine). **More than about 20.3 mm means something in the socket is stopping the heel**, and the shroud frame then cannot reach its chainplates.
   - No glue is needed, so the mast lifts out for transport. A drop of CA in each pocket makes it permanent.
   - **If the mast stops high (prints from v7m or earlier):** the slicer filled the socket in the lower half with a support column. Clear it with a **2 mm drill bit turned by hand only**, no power drill:
     - on a loose lower half, drill into the socket from the seam face and stop **5.8 mm below the seam face**;
     - on a hull that is already glued, drill down through the deck socket and stop **26.5 mm below the top of the deck collar**.

     Those depths bring the bit exactly to the socket floor. Under the floor is the solid mast step, 8.7 mm of plastic down to the hull skin, so a slight overshoot does no harm, but stop there. Pick out the loose strands with a pin, scrape the elephant-foot lip off the socket mouth, then try the 19.5 mm gauge again. The v7m socket has only 0.15 mm per side; if the heel still binds, sand the heel lightly, not the socket.
7. **Boom.** Its five holes are numbered from aft: 1–3 take the clew of the full, medium and start sails, 4 the mainsheet, and 5 (next to the mast) the gooseneck lashing.
   - Tie a stopper knot in a 15 cm thread and pass it **down** through hole 5, so the knot sits on top of the boom.
   - Take it forward **under** the boom nose and twice round the mast, so the turns sit on top of the gooseneck saddle. Bring it back under the boom, up through hole 5 again, and tie it off against the knot.
   - Pull it tight, so the boom nose just touches the back of the mast. Because the legs leave from the **underside** of the boom, any push down on the boom nose (the mainsheet does that) tightens them, and they hold the boom level with the saddle. The saddle stops the turns sliding down the mast; the boom itself does not rest on it.
   - The boom must still swing freely to either side (it clears everything to ±45°). If it binds, ease the lashing a little.
   - The mainsheet runs from hole 4 down to the coachroof eye (see Paper sails).

   ![Boom lashing at the gooseneck](views/details/gooseneck.png)
8. **Furled genoa (display only).** Its head ends in a flat J-shaped tang that drops into a slot in the masthead cap, behind a small lip. The slot walls hold it sideways and the lip holds it fore-aft, so it does not wobble.
   - **Seat the mast fully first** (gauge 19.5–19.8 mm, step 6). If the mast stands more than about 1 mm high, the foot tab can slip out of its pocket while you fit the head; at 2 mm high it no longer reaches.
   - If the paper mainsail is on, tie its head first, with the knot aft of the mast and no turns over the top of the cap, so the slot stays clear.
   - Put the navy foot tab into the stemhead pocket on the bow.
   - Hold the head about 1.5 mm above the cap, with the tang over the slot, and lower it straight down. Let go: gravity seats it on the slot floor behind the lip.
   - **To take it off,** lift the head **straight up** about 1.5 mm (at least 1.1 mm, to clear the lip), then move it forward. Pulling it up along the stay can jam the tang against the back of the slot.
   - Seated, the head has about 0.2 mm of play fore-aft and 0.25 mm each side. No glue is needed; a drop of glue in the slot makes it permanent on a shelf model. If the tang binds, take one stroke of a fine file off the aft face of the lip.
   - Take it off before sailing. The white body butts onto the navy drum; if they ever part, a drop of CA glue rejoins them.

   ![The furler's head tang in the masthead slot (section through the slot, true scale): seated, lifted 1.6 mm, then out forward. The gap under the cap is the sail-head tie hole.](views/details/masthead-joint.png)

   ![Masthead from forward: the tang in its slot behind the lip](views/details/masthead.png)
9. **Cleats** are printed into the deck, so there is nothing to fit.

## Stern and decks

- **Open stern:** the cockpit sole steps down to a full-width teak bathing platform, set into a reverse-raked transom (~8°). The folding swim ladder lies stowed fore-aft on the platform, in navy relief.
- **Teak:** cockpit sole and seats, side decks and foredeck. Planks spring parallel to the deck edge and are **nibbed** square into the king plank and coachroof margins at the bow, as on real teak decks.

## Cleats, and why there are no railings

- **No railings.** v7h had printed navy railings (pulpit, stanchions, lifelines and pushpit): fences 0.68 mm thick with 1.0 mm posts, glued into 20 deck pockets. They were removed in v7i, on the owner's call and with all three reviewers agreeing. At 1:66 a real stanchion is 0.38 mm and a lifeline 0.09 mm, so the thinnest posts a 0.4 mm nozzle prints read as a fence, not as wire. The navy toe rail along the deck edge, the cleats and the chainplates now carry the edge detail, and the teak runs unbroken where the pads were.
- **Cleats:** six navy horn cleats are printed into the deck, each 0.4 mm inside the toe rail and turned to follow the deck edge, where the real boat has them. They moved in v7n: before, the bow pair stood 9 mm off the centreline of the foredeck, the middle pair 24 mm aft of the widest point, and the middle and stern pairs 3–5 mm in from the edge.
  - **bow pair**, 24 mm aft of the stem (1.6 m on the real boat), angled 26° as the bow narrows;
  - **spring pair** at the widest point, 108 mm aft of the stem, square to the hull;
  - **quarter pair**, 14 mm forward of the transom, angled 8°.

  Each is 4.2 × 1.2 mm and 2.72 mm tall on a 3.0 × 1.6 mm flange, with the teak cut round the flange so the cleat stands on white deck. A short straight waist leaves daylight under each horn, and every overhang is 45° or less, so no supports are needed. The earlier cleats were white on white cut-outs in the teak, which made them invisible.

  ![Cleats on the deck plan](views/details/deck-cleats.png)

## Bow anchor and transom name

- **Anchor:** a navy delta anchor lies stowed on the bow roller, and reads as a separate fitting although it prints as part of the white upper hull (nothing to glue):
  - its 1.0 mm shank runs over the roller between the cheeks with 0.65 mm of daylight each side and 0.9 mm of air under it;
  - it rests only on the roller and, through a D-ring shackle, on a small white deck chock;
  - the fluke hangs ahead of the stem with a 0.75 mm shadow gap and touches it only at its toe, which is where its print starts. The crown stands about 1.5 mm proud of the cheeks.
  - It stays inside the 200 mm length and adds no supports.
- **Name on the stern:** **Margaret** is inlaid 0.8 mm into the port transom face, beside the walk-through to the bathing platform, and reads left to right from astern. It matches the bow names (navy, bold).
- A small white pad inside the transom keeps 0.85 mm of white behind the letters. Shallower inlays (0.4 and 0.6 mm) looked fine in Blender but sliced into broken navy fragments; test coupons showed 0.8 mm is the depth at which the slicer prints every stroke. The real plate's G-code was checked letter by letter: every stroke of every letter prints on every layer (`data/transom_gates.json`).

## Rig and sails: display or sailing

**In short:** the whole rig is printed and needs no thread stays. The mast stands in its keyed blind socket. A flat navy **shroud frame**, printed in one piece with the mast, carries the cap shrouds from the hounds over both spreader tips, and the lower shrouds, down to chainplates **near the deck edge** (±26.0 mm, 86 % of the half-beam, just inboard of the toe rail), as on the real boat. The spreaders are widened to match: 24.0 mm half-span lower, 14.5 mm upper. There is no backstay: a printed split backstay does not fit on the plate, and the masthead is too thin for a clip, so the rig carries only what can be printed. The forestay is suggested by the printed **furled genoa**, keyed into the masthead. The paper sail weighs about 0.5 g, so she floats on her line and sails; the printed display sail weighs 4.5 g, so it is for the shelf.

| Purpose | Rig | Sail |
| --- | --- | --- |
| **Sailing** | Printed mast + shroud frame, boom; furler **off** | Paper (start / medium / full), 0.5–0.7 g |
| **Display** | The same, plus the printed furled genoa | Paper full sail, or the **printed display sail** (plate 4) |

- **Scale honesty:** the shroud strips are 1.0 × 0.6 mm, about 66 mm thick at full size, which is what a 0.4 mm nozzle prints reliably. They read as rigging in navy, and they brace the mast sideways without any tensioning.
- **Furler:** a 226 mm white furled genoa on a navy drum (3.8 × 2.8 mm). Its D-shaped section is 2.6 mm wide at the drum, 3.4 mm at the belly and tapers to 2.3 mm at the head; it prints 2.0–2.4 mm tall. Its foot tab sits 3.2 mm deep in the stemhead pocket (0.2 mm clearance). At the head, a 1.0 mm J-shaped tang drops into a 1.5 mm slot in the masthead cap, behind a 0.6 mm lip (Assembly step 8). Before v7o a hook hung over the cap with nothing holding it sideways, so the head could swing about ±18 mm.


**Sail markings (paper and printed):**
- The sail number is **MGT 43** (code over number), in 6.8 mm capitals: the racing-rules minimum of 450 mm for a boat over 11 m, at 1:66. Two navy waves near the head are Margaret's insignia. Two reef rows show cringle patches and reef points.
- As on a real mainsail, each side carries its own set: the **port** set is lower and reads normally from port; the **starboard** set is higher and reads correctly from starboard. On the paper template the starboard set is printed mirrored, so it reads through the taped sheet.
- The marked paper main is shown in `Margaret-views.png`. To use another code or number, set `SAIL_CODE` / `SAIL_NO` before running `display_sail.py` and `presentation_v7.py`.

**Printed display sail (optional):**
- The same outline and holes as the FULL paper sail: 0.52 mm white PLA with seven cross-cut seams, four battens, raised tabling and corner patches on the starboard face.
- **Markings in navy:** the port number is inlaid into the first layer (crisp on the bed face); the starboard number is a 0.16 mm relief on a seam-free panel (seams stop 0.6 mm short of the numbers); the wave insignia goes through the full thickness.
- 66.9 cm², 4.5 g. It prints on plate 4 next to the stand.
- Print flat as sliced, no supports. Let the plate cool before peeling it off, then peel or snip off the three Ø10 mm mouse ears at the head, tack and clew (they only stop the corners lifting).
- Tie it on exactly like the paper full sail (same holes, same thread).
- **Don't sail with it.** It is about 8× the paper sail's weight, high up: it raises her centre of gravity by about 7 mm and cuts the metacentric height from 16.0 to about 9 mm. She still floats upright, but heels much more. Swap to paper before she goes in the water.
- If the starboard number prints faint on your printer, rebuild with a 0.24 mm relief (`display_sail.py`, one more layer).

## Paper sails

Print the PDF at **100 %** and check the 50 mm bar. Use 80–100 g/m² paper. The grey lines inside each outline are cloth detail (seams, battens, tabling, corner patches, reef rows); the navy marks are the sail number and insignia. Cut on the black line; the labels stay on the waste paper below the foot. Laminate both faces with **matte** clear tape (it waterproofs the sail and keeps the grey seams visible without shine), then pierce the marked holes. The full sail weighs ≈ 0.5–0.7 g with tape and is already in the 64 g budget.

1. **Head:** tie the reinforced head hole to the masthead hole (full sail; knot aft of the mast, no turns over the top of the cap, where the furler's tang sits), or round the mast just above the upper spreader (start and medium).
2. **Luff:** a small thread loop through each luff hole and round the mast, every 20 mm. Keep them off the spreader roots (dashed marks).
3. **Tack:** lash the tack hole round the mast just above the boom.
4. **Clew:** tie it down to the matching boom hole. The boom has five holes, numbered from its aft end: full sail hole 1 (70 mm aft of the mast), medium hole 2 (58 mm), start sail hole 3 (46 mm). Hole 5, by the mast, is the gooseneck lashing.
5. **Mainsheet:** from boom hole 4 down to the eye on the coachroof below it. Tie it so the boom sits about 15° off the centreline to start.

| Sail | Area | Heel at 1 m/s | Heel at 1.5 m/s | Heel at 2 m/s | Heel at 3 m/s | Use |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| **Start** | 26 cm² | 1° | 3° | 4° | 10° | First trials, normal light breeze |
| Medium | 32 cm² | 1° | 3° | 6° | 12° | Steady light air |
| Full | 66 cm² | 4° | 8° | 14° | 29° | **Only below ≈ 1.5 m/s**, or display |

The deck edge goes under at about 31° of heel, so the full sail is nearly there at 3 m/s. Above about 3 m/s (a fresh breeze that ruffles the water everywhere) none of the paper sails is calculated to be safe: keep her ashore or try only the start sail on a retrieval line.

The sail's centre of effort is slightly ahead of the keel's centre of lateral resistance (4 mm with the full sail, 12 mm with the start sail), so she may bear away. Turn the rudder's trailing edge a few degrees to windward and ease the sheet until she sails straight.

## Ballast (detachable bulb, 3 mm lead balls)

The bulb splits at a horizontal glue plane. The **upper half (fin cap)** is part of the fin. The **lower half (cup)** is a hollow shell with 0.9 mm walls. Two Ø2.1 mm posts in the cup locate it in Ø2.4 mm holes in the cap (0.15 mm per side in the model, about 0.12 mm as printed). They stop it rotating, but they do not hold it on.

1. **Weigh** the finished, rigged boat without lead and without the furler. Lead target = **63.9 g − that mass** (≈ 12.0 g ≈ 75 balls at 0.16 g each).
2. **Pour the lead in level** (the cup standing upright) and press the cup onto the cap. **Tape the seam all round with waterproof tape** for trials; the bulb stays fully detachable.
3. **Float it in a tank.** The water should sit just under the blue/white line, level fore and aft. Check that she rights herself from a gentle heel to both sides.
4. **Sail on a retrieval line**, start sail first.
5. **Close the bulb for good.**
   - Lock the balls with a little thin epoxy (counted in the 0.4 g bulb-glue allowance).
   - Glue the cup to the cap with epoxy on the full rim.
   - Repeat the float test.

**Lead safety:** use intact balls; never cut, sand or heat lead. Keep it away from children and pets, wash your hands after handling, and seal it fully in epoxy.

## Display stand (plate 4)

A swan-neck stand, like a model-aircraft stand. It has a thin egg-shaped base and **one** curved neck that **rises from aft, between the rudder and the keel**, then leans forward into a small fork under the hull and lifts her up. Nothing enters the model: no pins, no glue. Three reviewers on different models designed it and then challenged it (see `REVIEW.md`, Steps 11–12).

- **Size:** 96.5 × 63.8 × 54.1 mm overall.
  - The base is a 1.4 mm egg with a bevelled top edge, wider under her centre of gravity and narrower aft under the neck root.
  - The neck is 6.5 × 5.6 mm at the root with a 4 mm root fillet. It rises vertically 3.7 mm behind the bulb tail, then leans 48° forward up to the fork. It stays 21.9 mm clear of the rudder.
  - The bulb floats 8 mm above the base.
- **How it holds her:**
  - The fork's two pads, 36 mm long, follow the hull bottom either side of the keel with zero gap, and carry her weight.
  - The keel root sits in the fork slot with 0.4 mm per side, so she cannot roll (≈ 0.6° of play).
  - The fork is closed just behind the keel's trailing edge (0.5 mm), so she cannot slide aft.
  - Nothing locks her going forward, and nothing touches the bulb. The low point of the hull bottom lies inside the pads, so they form a shallow cradle: to move forward she must first rise 0.13 mm over 9.5 mm (0.8° on average). With PLA-on-PLA friction (μ ≈ 0.3, assumed) she stays put up to about **17.5° of forward tilt**, and it takes a push of about **0.2 N** (a firm finger flick) to start her sliding. Her centre of gravity stays over the pads for the first 8.6 mm of any slide (7.4 mm without lead).
  - The v7h bulb-nose saddle was removed in v7i. A catch on the fork tips was also studied and rejected: the slot there is 15 mm wide so the bulb can pass on lift-off, and anything big enough to catch the 2 mm fin would block the bulb's way out.
- **On and off:** lift her 3 mm, slide her 29 mm forward, then lift her away; put her on in reverse. The fork's slot opens forward in a V, so the bulb passes up through it. A check of 728,625 vertex positions along that path found no contact, and the rudder stays 2.8 mm from the neck at the end of the slide.
- **Calculated, not yet measured** (full lead / no lead / printed display sail):
  - her centre of gravity is 8.6 / 7.4 / 8.5 mm inside the front end of the pads;
  - the whole assembly tips sideways at 30° / 27° / 28°, forward at 32° / 29° / 29°, and aft at 49° / 45° / 46°.
  - **Neck strength:** each horizontal print layer of the neck was sliced from `Stand.stl` and checked for bending plus compression from her weight acting at her centre of gravity (σ = M·c/I − W/A). The worst layer, at the start of the forward lean, sees 1.4 MPa of tension with the 68 g display-sail load. That is a safety factor of **10.6** against a conservative 15 MPa layer-bond strength, and still 3.5 if the shelf is knocked hard (3 g). The fork sags about 0.6 mm under her, about 1.2 mm if PLA creep doubles it over time. With the paper sail the factor is 11.3.

  Check these after printing: the base sits flat, and with her on the stand, tilt it 10° nose-down (with and without lead); she must not creep.
- **Print:** plate 4 of `Margaret-P2S.3mf`, together with the printed display sail (1 h 12 min for the plate).
  - One piece, standing upright, in navy PLA, 15 % infill, 3 walls.
  - Tree supports sit only under the fork head, whose underside is hidden under the hull. The base, fillet and neck print without supports; the steepest unsupported face is 49°.
  - **10.6 g finished** (about 12.3 g with its supports).
- **Use:** fit the bulb (taped or glued) before putting her on. **Lift her off before moving the stand**: nothing locks her going forward. Optional felt pads under the base protect the table.
- **Rig and tune the sail off the stand.** Don't tie the sail or fit the furler while she sits on it.

## Rebuilding (optional)

All scripts are in `scripts/` and expect Blender 5.2 and Bambu Studio on macOS. Run them in this order:

1. `MARGARET_OUT=build blender -b --factory-startup -P build_v7.py` (generator; needs `hullgen.py` and `hull_params_v7.json` beside it).
2. `MARGARET_OUT=build blender -b --factory-startup -P check_v7.py` (fits: rudder, wheels, shroud feet, furler tang and tab, cup/cap), then `plate_v7.py` the same way.
3. In `build/plate`: `MARGARET_WORK=$PWD python3 prepare_slice.py`, then Bambu Studio's CLI assembles the four plates (`--load-assemble-list plate.json --export-3mf assembled.3mf`), `patch3mf.py` gives each object its real name, its own filament and its per-object settings (mast-bore support blockers, stand supports), and a second CLI call slices all plates (`--slice 0`). `gcode_mass.py` and `plate_times.py` then read the G-code into `mass.json` and `times.json`. Plate 4 needs the stand and display sail already built in `build/stand` and `build/dsail` (steps 5 and 7).
4. `SLICE_MASS=build/plate/mass.json MARGARET_OUT=build python3 hydro_check.py` (float, trim, righting curve), and `stability_v7.py` in Blender with the same variables (sails, heel, CE/CLR).
5. Display sail (before the plate and the renders, which use its markings on the paper-sail preview): `MARGARET_OUT=build SAIL_OUT=build/dsail blender -b --factory-startup -P display_sail.py`, then `./stand_slice.sh <abs path to build/dsail> Display_sail-bed.stl Margaret-display-sail.3mf 1 "Margaret display sail"` (this one-part slice only feeds its mass to the stand's tipping figures; the print itself is plate 4). `SAIL_DIR=… SAIL_IMG=… blender -b --factory-startup -P sail_show.py` renders both faces.
6. `present_v7.py`, `float_v7.py`, `closeups.py` (renders), then `presentation_v7.py` (sheets and PDF).
7. Stand: `MARGARET_OUT=build STAND_OUT=build/stand DISPLAY_SAIL_JSON=build/dsail/display_sail.json blender -b --factory-startup -P stand_neck.py` (the build stops if any clearance, lift-off or overhang check fails), then slice it twice:
   - `SUPPORT=1 ./stand_slice.sh <abs path to build/stand>` slices the stand alone with tree supports (for its mass with supports; the print itself is plate 4);
   - `./stand_slice.sh` on a copy of `Stand-bed.stl` in a temporary folder, with its `slice/times.txt` copied to `build/stand/slice-nosupport/times.txt`, gives the finished mass without supports.

   Run `stand_neck.py` once more so it uses both masses, then `MARGARET_OUT=build STAND_DIR=build/stand DISPLAY_SAIL_JSON=build/dsail/display_sail.json python3 stand_strength.py` for the neck stress (`stand_strength.json`). Then `STAND_DIR=… SAIL_DIR=… blender -b Margaret.blend -P stand_show.py` adds the stand and display sail to the blend and renders them; run `presentation_v7.py` again for the stand sheet.
8. Name gates on the sliced plate: `python3 coupon/transom_gates.py build` (must print PASS) and `python3 coupon/namecheck.py build preview.png`.
9. Joint fits: copy `scripts/review14/` into a folder holding `yacht-build/<tag>/` (a build with its plate sliced and unpacked to `plate/x/`), then run `python3 review14/fits_stl.py <tag>` (model clearances), `fits_gcode.py <tag>` (as printed, from the toolpaths), `post_detail.py <tag>`, `bore_pinch.py <tag>`, `wheel_bore.py <tag>`, and `fit_sections.py out.png` (the v7j/v7l section sheet).
10. Rev-17 gates, the same way from `scripts/review17/`: `python3 review17/mast_fit_gcode.py <tag>` (mast heel vs bore on the toolpaths), `support_probe.py <tag>` (nothing but the loose first-layer strand inside the mast bore), `column_compat.py` (v7m vs v7n lower hull, ray-cast every 0.1 mm), and `MARGARET_OUT=build blender -b --factory-startup -P probe_v7n.py` (seating gauge and rudder-tube wall).
11. Rev-18 gates from `scripts/review18/`: `python3 review18/tang_fit.py <tag>` (furler tang in the masthead slot: parked gaps, drop-in path, lift to release, settling under gravity, mast standing high), `slot_gcode.py <tag>` (slot, cheeks, lip and tang on the plate-3 toolpaths) and `joint_section.py <tag> out.png` (the section sheet).

`run_chain.sh <tag>` runs everything from `plate_v7.py` in step 2 through step 6 plus the close-ups, after the build, the check, the display sail and the stand (paths at the top of the script point to the author's machine). The earlier raked-wall stand generator (`stand_v7.py`) is in the git history (commit `6378dd0`).

## Status

The design has been modelled and checked digitally:
- all parts are manifold, with no tiny colour islands
- clearance and swing checks pass, with **0 mm³** overlap between the cup and the cap; the furler's head tang sits in its masthead slot with 0.18–0.25 mm all round and needs a 1.1 mm lift before it can come out, and the shroud feet clear their pockets by 0.21 mm
- the plate has been sliced, and the per-part G-code mass was fed back into the float calculation
- the G-code was checked layer by layer to prove both names print legibly
- every joint (fin socket, rudder bore, bulb posts, wheel bores) was measured on the sliced toolpaths, not only in the model; small holes still print smaller than their toolpaths show, so the rudder bore now has 0.25 mm of running clearance per side
- buoyancy, trim and the righting curve were computed independently from the exported STLs
- the stand's on/off path, clearances, overhangs, forward hold, tipping angles and neck stress were computed from the same geometry
- all of the above was challenged by several independent model reviewers (see `REVIEW.md`).

**Test prints so far** (v7i/v7j hull halves, then a v7m set) showed these problems, all fixed:
- the blue bottom was too thin (1.2 mm since v7j);
- the Ø2.1 rudder bore did not take the stock (Ø2.5 since v7l, plus the drill pass for halves already printed);
- the v7l furler was too thin to print (thicker since v7m);
- in v7m the fin and the ballast cup opened in Bambu Studio as white, and the mast did not go home, so its shroud frame stopped short of the chainplates. The slicer had filled the blind mast socket with a support column. v7n sets each object's own filament, blocks supports in the mast bore, gives the mast 0.25 mm per side and moves the cleats to the deck edge (Assembly step 6 clears the socket of a v7m print);
- the v7m/v7n furler's hook hung over the masthead with nothing holding it sideways, so the head swung about ±18 mm, and it could not reach the cap at all with the mast standing 2 mm or more high. v7o keys the head into a slot behind a lip (Assembly step 8).

**She has not yet been leak-tested or sailed.** The ball count, trim, heel, fit and tipping figures are calculations. Confirm them in the tank and on a test print before gluing the bulb shut.
