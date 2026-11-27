# Margaret — Revision 17 round-1 challenge/defend brief

Margaret is a 200 mm (1:66) 3D-printable free-sailing model yacht styled like (not a copy of) a Jeanneau Sun Odyssey 43
(Lombard, ~2001): blue underwater body, white topsides, teak deck, navy details. Printed in PLA on a Bambu P2S (0.4 mm
nozzle, 0.16 mm layers, 4 AMS colours: 1 white, 2 blue, 3 navy, 4 teak). Two hull halves glued at a seam (z = 2.5 mm),
detachable lead-filled bulb (Fin_cap + Ballast_cup) glued back, spade rudder, printed mast + flat navy shroud frame whose
two foot tabs drop into chainplate pockets, display furled genoa, paper or printed sails, swan-neck display stand.
The owner has ALREADY PRINTED the hull halves and the v7m rig. Generator: files/build_v7.py (Blender bpy). Current
release v7m. Model coordinates: x forward (prescale; exported x is scaled by 1.0346), y port, z up, DWL z = 0.

## User requests this round
1. "put cleats in the correct places on the body"
2. "run the model through several models checks and dispute on the correctness, proportions, sea worthiness"
3. One 3MF, split by plates: (1) upper hull; (2) lower hull + keel (fin cap, ballast cup) + rudder; (3) mast(s) and
   steering wheels; (4) the rest grouped by colour. Keel/ballast "for some reason are white" — fix.
4. "I could not find the model for the boom and its connection to the body"
5. "I inserted the mast, but the rigging does not reach its fixing points on the body, maybe it did not go that far in"

## Evidence and proposals (defend or challenge each)

### A. Rigging does not reach the chainplates (root cause found in the sliced G-code)
- The lower hull prints upside down (seam face on the bed). The mast socket below the seam is blind: z -3.3 .. +2.5
  (5.8 mm). The slicer (supports "on build plate only", normal auto) filled it with a 2.95 x 1.82 mm support column,
  5.6 mm tall, with interface layers bonded under the socket floor. The upper hull's through-bore also gets a
  first-layer support skin at the seam face.
- Unless that column is drilled out, the mast heel stops at the seam, 5.8 mm high. The shroud tabs are designed to
  enter their pockets 2.0 mm (tab bottom 0.5 above the pocket floor), so the frame feet end ~3.8 mm ABOVE the
  chainplates — exactly the user's symptom.
- Designed bore clearance is 0.15 mm/side (bore 3.9 x 2.9, mast heel 3.6 x 2.6, ~30 mm engagement through the
  glued seam). As-sliced toolpaths: bore 4.04 x 2.91, mast heel 3.72 x 2.59 (x includes the 1.0346 scale).
- Proposed fix: (1) support-blocker volumes over both mast bores in the 3MF (tested: column gone, the socket roof
  prints as a 2.9 mm bridge; a loose 0.2 mm first-layer loop remains on the bed, not bonded to the part);
  (2) bore clearance 0.15 -> 0.25 mm/side; (3) 0.3 mm seam-mouth chamfer on both halves (elephant foot);
  (4) README: for the already printed lower hull, drill the support out of the socket (2 mm bit by hand, 5.8 mm
  below the seam face; if glued, from the deck through the bore) + a depth check (mast fully home = gooseneck
  saddle at a stated height above the collar). Tabs keep 0.2 mm side clearance in the pockets (digital check).

### B. Cleats (currently 6 navy horn cleats, 4.2 x 1.2 x 2.72 mm, fore-aft, on a 3.0 x 1.6 flange)
Current prescale centres: bow (79, +-9) inboard by the anchor locker; mid (-30, +-25) at the cockpit front; stern
(-78.6, +-23.5). Deck outer half-beam (measured): x 80: 14.7, x 76: 17.1, x 72: 18.9, x 0: 31.5, x -10: 31.7,
x -30: 31.6, x -70: 29.3, x -78.6: 28.4, x -82: 27.9. Toe rail inner face ~0.85 inside the outer edge.
So the mid cleats are ~6.6 mm (0.44 m full size) and bow cleats ~6 mm inside the edge: they read as inboard
deck fittings, not mooring cleats.
Proposal (SO43-like 6-cleat layout, each cleat ~0.6 mm (4 cm) inside the toe rail, long axis parallel to the local
toe-rail line so lines lead fair): bow pair at x ~76 just aft of the pulpit/anchor locker (edge angle ~25-30 deg),
spring pair at max beam x ~ -6 (aft of the shrouds at x 21.5, forward of the cockpit), quarter pair at x ~ -80.
Centre y = local outer half-beam - 2.3. Keep size (4.2 mm ~ 0.28 m full size; real SO43 bow cleats ~13 in = 5 mm).
Must stay support-free (horn undersides 45 deg), clear of chainplates, toe rail, teak, winches, coamings.

### C. Boom and its connection
The boom exists (Boom.stl, white, 71.6 x 1.9 x 2.6 mm, 5 vertical 0.84 mm holes) and is on the plate, but the 3MF
names objects "assemble_N", so the user could not find it. Connection today: the boom rests on a printed gooseneck
saddle on the mast at z 43; a thread loop goes through the boom's forward hole and round the mast (swing checked
clear through +-45 deg); a thread mainsheet runs from the 4th boom hole to a printed eye on the coachroof.
Options: (C1) keep the thread gooseneck (standard on small model yachts; the mast prints on its flat aft face so no
printed pin/tang can project aft) + name the object + a labelled close-up render and assembly figure;
(C2) a printed jaw (fork) on the boom that straddles the mast above the saddle with a tie across the front
(limits swing on a D-section mast, fragile prongs ~0.9 mm). Recommendation: C1.

### D. One multi-plate 3MF (tested with the CLI: 4 plates slice; per-plate prime tower position array needed)
Plate 1 upper hull (white/navy/teak) 6h55m; Plate 2 lower hull + Fin_cap + Ballast_cup + Rudder (blue/white/navy)
2h41m; Plate 3 mast+shroud frame, furler (display genoa), boom, two wheels (white/navy) 42m; Plate 4 the rest by
colour: navy stand (needs tree supports touching the model) + white/navy display sail. White keel cause: the
assemble list gives single-part objects (Fin_cap, Ballast_cup) only a part-level filament; the object-level filament
stays 1 (white), so Bambu Studio shows them white and a GUI re-slice would print them white. Fix: patch the 3MF
object metadata (object extruder + real names "Fin_cap", "Boom", ...; per-object support settings for the stand),
then re-slice the patched 3MF with the CLI and verify per-plate tool usage in the G-code.

### E. Correctness / proportions / seaworthiness — dispute these numbers
- LOA 200.0; hull 197.5; beam 63.4 (max outer half-beam 31.7); scale draft 30.3 mm but the model's bulb bottom is at
  z -55.45 (deep fin + 66 x 17 x 16 mm bulb, accepted by the owner for sailing stability).
- Mast top z 240 (real I ~ 17.7 m ~ 268 mm; P 15.25 m ~ 231). Paper main 66.4 cm2 (luff 188, foot 70.5 mm).
  Spreaders 2 sets (z 95, 155), chainplates at y +-26 (86% of half-beam), shroud frame 0.6 x 1.0 mm.
- Mass: PLA on board 50.3 g + extras 1.8 + lead 11.84 g (74 x 3 mm balls) = 63.9 g; displacement at DWL 63.9 g;
  trim 0.08 deg bow down; G z -3.5, B z -10.6, GM 15.9 mm, GZ max 10.8 mm at 85 deg, AVS 132 deg; deck edge immerses
  at 31 deg, cockpit floods at 130 deg; CLR (-6.1, -19.6); lateral area 34 cm2; reserve buoyancy 165 g;
  cavity holds up to ~20 g lead discrete (127 balls). Hull wall 0.85 topsides / 1.2 underwater.
- Seaworthiness questions: leak paths (mast socket is blind in the lower half; rudder bore runs to z 11 above DWL;
  seam glued), weather/lee helm (CE vs CLR), whether the boom thread gooseneck and the paper main survive light air,
  whether the 0.6 mm printed shroud frame is a credible load path or just display.

Images to inspect (view tool): /Users/stanvasilyev/projects/pet/3d_design/Margaret/views/1-starboard-bow-quarter.png,
2-port-profile.png, 3-starboard-profile.png, 4-cockpit-helms-teak.png, 5-deck-plan.png, 6-ballast-bulb-exploded.png,
views/details/*.png, Margaret-sail-rigging.png, Margaret-afloat.png. Numbers: Margaret/data/*.json.

## What to return (<= 600 words)
For A–E: AGREE / CHALLENGE with specific reasons and concrete numbers. Rank material fixes only (things that would
make the print fail, mis-assemble, look clearly wrong vs an SO43, or be unseaworthy). Avoid hull-shape changes unless
clearly justified — the owner has printed parts (the cleat change already forces an upper-hull reprint).
Do not propose new tooling or process. State a final GO / NO-GO for proceeding with A–D as proposed.
