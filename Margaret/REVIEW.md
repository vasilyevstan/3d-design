# Margaret revision 2: review log

Coordinates are model mm. The bow points +X, port is +Y, and the design waterline (DWL) is z = 0. The model is 200.0 mm long overall: the stern platform lip is at x = −100 and the tip of the bow roller is at x = +100.

## Step 0: critiques of draft 1

Three reviewers critiqued draft 1, each on a different model:

| Reviewer | Model |
|---|---|
| Naval / look | Claude Opus 5.5 |
| Printability | GPT-6.2 Sol |
| Design | Grok 4.7 |

All three agreed on these root causes:

- **Faceted hull.** The hull was built from 7 waterline rings joined by flat strips, with 3 height rows in the topsides, so it creases at every row. Smooth shading hid this in renders, but the STL keeps the facets.
- **Wrong proportions.** The sheer was flat at a freeboard of 10 mm, about half of scale. The sections were dish-shaped, flaring 29–34°. The stem was a knife edge.
- **Stern.** The transom raked the conventional way, with a glued-on slab and raised teak tiles on it. This was the "weird platform".
- **Deck joint.** The deck landing ring stuck out 0.2–0.37 mm through the topsides, and the deck sat 1.45 mm inside the hull edge, like a bathtub lid.
- **Coachroof.** It was a 12-sided polygon with a flat roof. Each side had four separate window slabs standing proud, and the coamings were boxes.
- **Keel.** The fin was flat-sided with a blunt trailing edge and a shoulder plate. The shoe was a bathtub shape with a 66° overhang.
- **Rig.** The mast socket was 3.7 mm deep. The forestay went to the pulpit, the shrouds to cleats 29 mm aft of the mast, and a single backstay to the starboard cleat.
- **Pipeline.** `model.py` silently reused MCP seed objects, so fixes could miss the STL.

## Step 0 synthesis: decisions for revision 2, open to challenge

### D1. Hull surface

- **Method.** Parametric Bézier sections (`hullform.py`), with every parameter a C2 spline along x. Use 170 stations, packed closer at the ends, and 72 points per half-section spaced by arc length.
- **Colour line.** An exact vertex row at the colour line.
- **Inner skin.** A true section-normal offset.
- **No smoothing modifiers.** No Subdivision Surface on the hull.
- **Checks.** Measure the largest angle between adjacent faces and run a zebra-stripe render.

### D2. Lines (`hull_params_v3.json`)

These follow Opus and Grok, slightly fuller.

- **Freeboard and sheer.** Freeboard is 18.5 at the bow, 14.5 amidships and 14.0–14.3 at the stern, against Opus 17/13.8/13.6 and Grok 18/14.5/13.6. The sheer rises 4.5 mm to the bow.
- **Beam.** Maximum beam is 63.4 mm at x ≈ −15, and the transom is about 48 mm wide at the deck.
- **Flare and bilge.** Topsides flare 11–13.5°. The bilge is firm amidships, and the aft sections are wide and flat.
- **Stem.** Straight, raked 19°. The forefoot blends into the keel line through a tangent arc of R 9 mm, avoiding a knuckle. The stem face is 1.8 mm wide.
- **Hydrostatics.**
  - Canoe-body volume 52.1 cm³ (draft 1: 52.2).
  - Waterline length 183.7 mm.
  - Waterline beam 55.2 mm.
  - Canoe-body draft 12.3 mm.
- **Transom.** Reverse transom. The lower edge (knuckle) is at x −97.5, z +1.2. The deck edge is at x −92.5, z 14.3. That is about 21° of reverse rake.

### D3. Print orientation and part split (my proposal; the critics didn't raise it)

- **Hull upside down.** Draft 1 printed the hull upright, so the whole shallow blue bottom (deadrise 5–15°) needed supports and would have printed rough. Revision 2 prints the hull **upside down on its sheer rim**:
  - The outer bottom and topsides then have no support contact at all.
  - The supports needed under the bottom are inside the hull. They stand on the plate inside the open deck opening and are removed through it.
- **Toe rail moves to the deck.** Because the hull rim is the build-plate face, the toe rail can't be the hull wall carried up, as Opus proposed.
  - The deck part overlaps the full rim.
  - A half-round rubbing strake on the deck edge, 0.35 mm proud, covers the seam on the sheer line.
  - A deck skirt drops 2.0 mm inside the hull, giving alignment, glue area and a seal. The deck prints upright with hidden supports underneath.
- **Rim deviation.** The sheer is not flat, so the hull is tilted to fit the plate best. The rim then deviates by up to about 1–1.5 mm, which needs short supports under parts of the rim. The rim is a hidden glue face.
- **Outward-facing up surfaces.** Every up-facing outer surface of the hull would face down when inverted. The only ones are the stern steps, so they move to a small separate **step insert**:
  - The insert prints upright with no supports and has teak inlays on the tread tops.
  - It glues into a sealed rectangular **walk-through well** in the hull, 20 mm wide.
  - The well floor is above the DWL, so the hull stays watertight on its own.
- **Inside features.** Overhangs inside the hull get auto-supports, and they're hidden. The mast tube and rudder tube rise to the rim plane, so they start on the plate.

### D4. Stern

- **Layout.** A centre walk-through 20 mm wide (|y| ≤ 10). Platform at z 2.6 from x −100 to −92.5; it projects 2.5 mm aft of the knuckle and its lip sets the length overall. Steps at z 6.3 and 10.0. Deck level forward of x −85.5.
- **Teak.** Flush tan tops, 2 layers thick.
- **Transom.** No name on the transom; the name goes on the bow, as the owner asked.
- **Wheels.** Twin wheels at x −80, y ±11, lined up with the walk-through.

### D5. Keel and bulb (Opus geometry, GPT print rules)

- **Fin.**
  - NACA 0013 trapezoid.
  - Root at z −12.3: chord 27, leading edge x +9, trailing edge x −18.
  - Tip at z −41.5: chord 19.5, leading edge x +2.5, trailing edge x −17.
  - Trailing edge 0.5 mm thick.
  - A tenon 18 × 3.2 × 5 into an 18.4 × 3.6 hull socket, set in a small flat root boss blended into the hull. The fin is glued into the hull permanently.
- **Bulb.**
  - NACA-thickness radius law, thickest at 30–35% of length.
  - 58 long, 15 wide, 12.5 high. Top at −41.5, widest line (the split) at −45, bottom at −54, so the draft is 54.
  - Elliptical cross-sections: flat-topped, with a full belly.
  - Nose at about x +15, tail at about −43. The position is fine-tuned by the hydrostatics script.
- **Cap and fin.** The cap is the bulb above the split, solid and part of the fin. It prints mating face down with the fin vertical, so the foil sections print crisp.
- **Cup.**
  - The cup is the bulb below the split, the **detachable weight part**.
  - Wall 1.1 mm, with solid nose and tail blocks.
  - It prints rim down, with no outer overhang.
  - The cavity is open to the plate, so any internal support comes out.
- **Joint.**
  - Full-rim glue face, plus two 1.75 mm filament dowels in Ø1.95 × 3.5 holes in the solid end blocks.
  - Tape or a rubber band holds the cup during float trials.
  - After trials, fix the lead with epoxy and epoxy the rim. Lead position inside the cup also trims the boat fore and aft.
- **Fillets.** 2 mm at the fin–bulb join; 1.5 mm at the root boss.
- **Estimated mass budget.**

  | Item | Mass (g) |
  |---|---|
  | Hull | ~24.5 |
  | Deck | ~15 |
  | Fin and cap | ~4 |
  | Cup | ~3 |
  | Mast and boom | ~2.7 |
  | Rudder | ~0.8 |
  | Step insert | ~1 |
  | Sail, thread and glue | ~1.5 |
  | **Total** | **~53** |

  Displacement is about 59, leaving **about 6–9 g of lead**: about 40–55 balls of 3 mm. The cavity holds 15 g or more, so there is margin. GM is about 15 mm, dominated by form stability. Recompute from the sliced masses.

### D6. Coachroof and deck

- **Coachroof.**
  - A smooth spline wedge from x −38 to the front of the roof at +46. Half-width 18.5 from x −30 to −5, narrowing to 10 at +40.
  - Roof at z ≈ 19.8 aft, 18.8 forward.
  - Windscreen raked about 57°, roof camber 0.8, sides leaning in 12°.
  - Edges softened by the dense loft, not by subdivision.
- **Windows.** One flush ink band per side, 0.5 mm deep, from x −31 to +30. It is 2.2 tall aft and tapers to 1.3, with two white mullions. Three flush ink windscreen windows.
- **Hatches.** Flush smoke-ink hatch tops with raised frames 0.3 mm high: one on the foredeck and two on the coachroof.
- **Deck.** Camber 1.1 mm. The cockpit well has seats and a sole with teak tops.
- **Coamings.** They run aft from the coachroof sides and step down to 2.5 above the deck by x −70. Two primary winches sit on the coamings and two on the coachroof.
- **Cleats.** Bow, spring and stern cleats with overhanging horns.
- **Toe rail.** A 0.8 × 0.7 rib along the deck edge.
- **Wheels.** 11 mm diameter with thin rims, set in floor slots so their lower arcs are hidden and need no support.
- **Left out.** Pulpit, pushpit, stanchions and lifelines are below printable size at 1:66 (the tube would be 0.4 mm), so they are omitted. That is stated in the README.
- **Hull ports.** Two slim flush ink ports per side (8 × 1.8 mm) at x 5–35, sharing colour-change layers with the bow name.

### D7. Bow name "Margaret"

- **Placement.** Both sides, as a flush ink inlay 0.45 mm deep, behind which the hull wall is locally thickened inward to 1.5 mm. Port and starboard are built separately so neither reads backwards.
- **Font.** Georgia Bold Italic, cap height about 3.8 mm. Upright strokes must be ≥ 0.6 mm; this is checked.
- **Position.** It starts about 18 mm aft of the stem, with the baseline parallel to the sheer, about 7 mm below it.

### D8. Rig: functional thread stays (answers the owner's question)

- **Mast.**
  - The mast stands by itself in a **blind, sealed tube** in the hull, rising from the floor to the rim, plus a collar through the coachroof. That gives about 30 mm of grip.
  - The tube is a rounded rectangle, so the mast can't rotate.
  - The mast prints lying on its leading face, so the spreaders lie flat.
- **Stays.**
  - Thread does real work: it keeps the mast straight and carries sail load to the hull.
  - Use 0.15–0.25 mm braided polyethylene fishing line.
  - Forestay to a stem fitting on the bow roller at x ≈ +97.
  - Two shrouds over the spreaders (z ≈ 95, reaching y ±16, swept aft 12°) to chainplate eyes at x +4, y ±26.5.
  - Split backstay to eyes at x −90, y ±18.
  - The masthead crane is 4.4 mm wide with two Ø1.4 holes. Deck eyes have Ø1.4 holes with ≥ 1.0 mm of material around them.
  - Tension: just taut.
- **Sail.** Paper main with 8 mm of roach and panel lines, tied at head, tack and clew.
- **Rudder.** NACA 0012, root chord 15, tip 10.5, elliptical tip, 8° sweep, 1.75 mm filament stock in a blind, sealed Ø1.95 hull tube.

### D9. Colours and colour changes

- **Four slots.** White, antifouling blue, ink (navy-black) and teak.
- **Waterline.** Blue up to z +0.6, then an ink boot stripe from z 0.6 to 1.4.
- **No cove stripe.** The rubbing strake defines the sheer.
- **Change count.** Colour changes are inherent on a single mixed plate. Keep the extra ink and teak bands thin.

### D10. Pipeline

- `model.py` rebuilds everything from parameters; no reused seed objects.
- Automated checks: manifold, minimum wall, largest angle between faces, volume and centre of buoyancy, length overall 200.0, colour line flat.

## Step 0 challenge/defend: print (GPT-6.2-sol challenger)

| # | Challenge | Verdict | Resulting change |
|---|---|---|---|
| 1 | Tilted sprung rim is not a reliable first layer (midships 1.8 mm off bed) | **Accept** | Planar hull/deck split at **z = 13.0** (horizontal, DWL parallel to bed). Hull prints inverted on a flat rim with a 6 mm brim. The lid carries the sprung sheer band (1.0–5.5 mm). |
| 2 | Straight skirt jams on the flared hull | **Accept** (by removal) | No skirt. Flat-to-flat joint with a 1.8 mm glue land (both parts thicken inward at the seam) and 1.75 mm filament dowels in Ø2.15 holes in rim lugs, mast tube and keel box for registration. Seam gets 0.3 mm chamfers on both edges: a deliberate fine shadow line. |
| 3 | One-plate not demonstrated for 8 parts | **Accept** | Delivery gate: reslice all parts on one plate, report model-only mass, swaps, first layer. |
| 4 | Budget supports 6.5 g not 9 g | **Accept** | Target sealed empty mass ≤ 52 g; report ballast from the slice. |
| 5 | Tilt widens the colour band | **Accept** | No tilt; colours as registered volumes. |
| 6 | GM alone doesn't prove sailing | **Accept** | Sail template gets a ≤ 30 cm² light-air outline; README: start ≤ 1.5 m/s, check 20° recovery; stern well drains aft, hull stays sealed. |
| 7 | Supports may trap around tubes / well floor | **Accept** | Cockpit + stern well floors are hull overhangs supported from the bed; their visible faces are covered by a separate **cockpit/stern insert** (teak sole, steps, platform, pedestals) printed upright and glued in, which hides the scars. All tubes/lugs grow from the bed (no hanging ends). Inspect removal lanes in slice. |
| 8 | Cup cavity roof sags rim-down | **Accept** | Cavity roof ≥ 45°, final bridge ≤ 4 mm; verify ball count by packing. |
| 9 | Dowel holes close at first layer | **Accept** | Ø2.15 bores, 0.4 mm chamfers, 5–6 mm pins; tape/wrap retention for float trials. |
| 10 | Collar preload; forestay at roller peels | **Accept** | Two keyed bearing lands 20 mm apart in the hull tube; deck/coachroof hole floats 0.5 mm/side. Forestay eye 4 mm aft of roller tip on a backed stem fitting; 0.20–0.25 mm braided line; proof-pull 0.5 N. |
| 11 | Fin root is a layer-adhesion test | **Accept** | ≥ 1.2 mm closed wall round the blind socket, solid tenon, README proof-load. |
| 12 | Terraces on low-deadrise bottom | **Accept** | 0.12 mm layers for the plate. |

Defended: inverted hull orientation itself (challenger agrees it is right once the rim is planar).

## Step 0 challenge/defend: look (Grok challenger)

| # | Challenge | Verdict | Resulting change |
|---|---|---|---|
| 1 | Stem too plumb/blunt for a 2001 Lombard hull; suggests ~16° rake | **Partly accept** | Rake 20° (see the Sonnet conflict below); stem deck point (97.6, 20.2). |
| 2 | Transom should be reverse-raked with an open walk-through | **Accept** | Transom 15° reverse rake, central walk-through with rounded cutters, step down to an integral platform. |
| 3 | Sheer too flat | **Accept** | More sheer spring: about 14.5 aft rising to 20.2 at the stem. |
| 4 | Rig proportions | **Accept** | Mast x 26, masthead z 250, two V spreader pairs (z 118 ±14, z 172 ±8), chainplates x 8 y ±30, split backstay to x −85 y ±21, forestay eye on the stem fitting, 0.20–0.25 mm braided line. |
| 5 | Deck detail | **Accept (next step)** | Twin Ø13.5 wheels x −66 y ±13.5 (printed separately, pin in the pedestal); pulpit/pushpit printed separately, stanchions about 0.9 mm, thread lifelines. |
| 6 | Bulb shape | **Accept (bulb step)** | Bulb about 50–52 × 12.5–13 × 10, bottom about z −34, fin chord about 26. |

## Seam pivot (designer, after the Step 0 print review)

The z = 13 split put a horizontal seam line across the visible topsides. Moved the seam to **z = 2.5**, the top of the boot stripe, where the colour change already draws a line. The lower tray (blue, white, ink bands) prints inverted on its flat rim; the upper body prints upright on its flat z 2.5 bottom. The 1.8 mm glue land and Ø2.15 lug pins are kept. The trade-off: the seam is now wet at heel, so the README requires an epoxy seal and a leak test.

## Step 1 challenge/defend: hull lines (Sonnet 5.5 challenger on v3)

No blockers. Proposed refinements and verdicts:

| # | Challenge | Verdict | Resulting change (v4) |
|---|---|---|---|
| 1 | Forefoot reads as a hook; curvature jumps | **Accept** | G2 clothoid-pair forefoot, R_min 11, solved tangent to the keel line: R ∞→194→51→…→11.8→…→85→straight. |
| 2 | Aft buttock has an inflection | **Accept** | Keel (−95, 1.38), (−89, 0.62); buttock R −405→−128, monotone. |
| 3 | Keel ridge too sharp amidships | **Accept** | Centreline round 1.5 mm amidships. |
| 4 | Waterline shoulders slightly hollow | **Accept** | Half-beam (55, 24.5), (75, 15.3), (90, 5.4): convex waterline. |
| 5 | Stem rake 24° from LWL/overhang data (conflicts with Grok's 16°) | **Compromise** | 20°: overhang and LWL stay within 1 mm of the reference, and the profile still reads modern. |
| 6 | Hydro: Cp 0.60, LCB −4.3, GM about 17–20; all-up CG must sit within ±2 mm of the LCB | **Accept** | v4: canoe 52.0 cm³, LCB +0.47. Fin x gets re-solved in the bulb step. |

Fairness gates (v4 outer): topsides max dihedral 3.82° (≤ 6), bottom 3.44° (≤ 8), centreline round 10.75° (tessellation of the 0.5–0.7 mm radius, not a crease). The slope-aware stem rounding fixed a 31.5° crease at x 95.5.

## Step 2: v4 assembly build

`build_v4.py` produces 7 manifold colour bodies: lower tray 10.27 cm³ and upper body 20.30 cm³, plus 0.25 cm³ of window panes, for 30.8 cm³ of PLA. Fixes made during the build:

- **Collection-operand booleans** produced non-manifold cavities, so all booleans are now sequential.
- **The cavity self-intersected at x 90**: the 1.8 mm glue-land inset is wider than the stem there. The cavity now ends at x 89, leaving the bow tip solid.
- **Colour bodies** are cut from shared tool solids, not from each other.
- **Lug holes** are placed adaptively, keeping at least 0.9 mm of outer skin.

Zebra renders are continuous over the topsides and bow.

## Step 2b — GPT-6.2-sol challenge of v4 (stern/cockpit) — defend/settle

| # | Challenge | Verdict | Outcome |
|---|---|---|---|
| 1 | Platform reads as slab/diving board | ACCEPT | Integral scoop: tread x −96.2..−88.5 z 4.8, half-width 12.5→10, R3, 1.4 lip, cheeks, underside blended to seam; no hinge |
| 2/3 | Cockpit = maze of rectangles | ACCEPT | yz-profile cutters: benches z 14.8, footwell 20 wide z 10.3, leaning backs, rolled shoulders, helm pocket, wheels (−67.5,±14,20) |
| 4 | Vertical coachroof aft block | ACCEPT | Raked aft face −38.5→−34, crown 23.0, half-width 18.5, lean 10°, R2.2 shoulder |
| 5a | Lift forefoot | DEFEND | G2 clothoid, R min 11.8 intended — conceded |
| 5b | Lower bow sheer 0.9 | DEFEND | 1.33 m / 0.96 m freeboard matches reference spring — conceded |
| 6 | Windows/ports/name proportions | ACCEPT | 3 panes, ports 7×1.8, name cap 3.2 x 54–74 |
| 7 | Toe rail 0.3 proud | SETTLED | 0.8 wide × 0.48 proud (4 layers), tapered ends |
| 8 | Teak overload | SETTLED | Teak only: 12 mm sole runner x −83..−40, bench tops, scoop tread; 0.8 inset; helm pocket white |
| — | Mass | ACCEPT | wall 0.85, deck 0.8, glue land 1.8; target ≤27 cm³ |
| — | LOA | ACCEPT | x-scale 194.4/192.6; bounds check 200.0 overall |
| — | Stem | ACCEPT | stem round 0.9, half-beam 1.0 |
| — | Rudder tube / mast blind bore / deck supports | DEFEND | already sealed/blind; supports through open bottom — conceded |
| — | 0.85 wall = 2 Arachne paths? | OPEN→delivery | Verify in slice at stem and inlays; verify support removal |

## Step 2c — independent v5 hull/cockpit challenge — defend/settle

| # | Challenge | Verdict | Outcome |
|---|---|---|---|
| 1 | Agreed low rolled scoop cheeks were missing | ACCEPT | Added mirrored cheek returns; clipped them 0.15 mm inside the reverse-transom plane so they don't alter its rake or leave a coplanar cap. |
| 2 | Rectangular coamings looked blocky and did not step aft | ACCEPT | Replaced them with swept profiles, 18.5 mm through the cockpit centre and smoothly stepped to 16.0 mm at both ends. |
| 3 | Cavity/color boundary at the narrow bow created a bad triangulated edge | ACCEPT | Cavity now terminates at x=80 (the forward 17.6 mm is solid); this avoids the narrow-stem offset/cap intersection. Blue/white split remains flat at z=0.8 mm. |
| 4 | In-memory manifold counts did not prove exported STL topology | ACCEPT | Triangulate before export, check all seven meshes, then reimport each actual STL: every file has zero non-manifold edges. |
| 5 | 0.85 mm wall needs proof of continuous slicer paths; z=2.5 mm seam is wet when heeled | ACCEPT / delivery gate | Verify stem/inlay wall paths and removal access in Bambu Studio. Epoxy-seal the assembled seam and leak-test before any float trial. |
| — | Hull size and mass | OPEN | Reference hull length is 194.4 mm, canoe displacement 52.95 cm³. Exported part volume is 31.49 cm³, above the 27 cm³ target; recalculate sliced mass and ballast allowance after keel/rig are designed. Bow fitting and scoop lip still need to set 200.0 mm overall. |

Defended: retain the smooth v4-derived hull lines and the z=2.5 mm split. The split is printable after sealing, but is not claimed watertight until physically tested.

## Step 3 — v5 detachable bulb challenge/defend

The NACA fin and bulb now export with the hull as two additional manifold bodies. The fin reaches z −44 mm, overlapping the bulb's upper cap by 2.5 mm; its tenon enters the hull to z −7.3 mm. The bulb is about 53 × 13 × 12.5 mm, with a detachable lower cup split at z −45 mm. The measured cup cavity is 1.291 cm³ after length scaling, estimated to hold 58 3 mm lead spheres (about 9.28 g) at an assumed 64% packing fraction.

| Challenge | Verdict | Outcome |
|---|---|---|
| Fin-to-bulb overlap was only 0.5 mm and concentrated stress at the junction | ACCEPT | Extend the NACA fin tip from z −42 to −44 mm, giving 2.5 mm of overlap into the bulb cap; re-exported fin/cap is manifold. This is a geometric overlap, not a separately modeled fillet. |
| Ballast allowance may be short if the finished boat needs more than 9 g | OPEN | Keep the current cup provisionally. The assembled external displacement is 59.015 cm³ at z=0 and 66.835 cm³ at z=1 mm, including the immersed keel; compare with the complete sliced mass and loaded waterline before freezing the capacity. |
| Pellet capacity assumes idealized uniform lead spheres and 64% packing | ACCEPT / physical gate | Treat 58 balls as a planning estimate only; verify with the actual 3 mm weights and leave room for adhesive. |
| The cup must remain removable for tuning and then be positively attached | ACCEPT / physical gate | Two chamfered pin bores register the seam; use temporary tape for tank trials and epoxy on the final assembly. The pin fit and bond are not physically tested yet. |
| Overall length was below the 200 mm target | ACCEPT | Scale the complete x-axis uniformly about its measured center; exported overall bounds are now 200.0 mm, while hull length is 197.21 mm (about 1.4% longer than the 194.4 mm reference-scaled target). |
| The current shell may leave little ballast reserve after rig and sail are added | OPEN | Exported print-solid volume is 36.212 cm³ (about 44.9 g at 1.24 g/cm³, before mast, boom, rudder, thread, paper and adhesive). Revisit from the actual slicer mass and do not claim stable sailing from this calculation. |

Defended: retain the streamlined bulb and the z −45 mm detachable seam for this iteration. Its 9.28 g estimate is in the earlier 6–9 g target range, and the assembled displacement curve shows room to load to the ink boot stripe; neither pellet packing nor loaded freeboard is proven until sliced and physically tested.

## Step 4 — rig and deck-detail challenge/defend

The current STL set has 14 manifold printable bodies: nine hull/keel colors, mast, boom, rudder and two helm wheels. Five deck stay eyes are fused to the hull; the mast has a head eye and two spreaders. The live Blender assembly also has a preview-only paper mainsail and five thread stays. The sail is 28.5 cm² with a 37 mm foot and 142 mm luff; thread and paper are post-print materials.

| Challenge | Verdict | Outcome |
|---|---|---|
| An upright mast would exceed or nearly fill the 256 mm bed | ACCEPT / plate gate | Keep the 240 mm mast as a separate flat-print part; confirm clearance, brim and prime-tower fit in the actual one-plate slice. |
| Rig lines could be cosmetic and leave the mast unsupported | DEFEND | Five preview stays run from the masthead/spreaders to the forestay, shroud and backstay eyes; specify real 0.20–0.25 mm thread after printing. Do not print the lines as STL. |
| The mainsail area might overpower the small ballast budget | ACCEPT | Reduced the paper-sail outline from about 34 to 28.5 cm². The final template must match the boom and include three tie/punch marks; begin physical trials in controlled light wind. |
| Rudder clearance and free adjustment are unproven | OPEN / fit gate | The printed 1.6 mm stock is paired with an approximately 1.85 mm blind tube and an accessible cockpit tiller. Verify stock fit and steering friction in the slice and dry assembly. |
| Helm wheels, winches, cleats and hatches were missing | ACCEPT | Added twin wheel bodies, six low cleats, four winch drums, two hatch inlays and integrated deck stay eyes. All additions are included in manifold STL validation. |
| Finished mass may leave little reserve at the color line | OPEN / hydro gate | All 14 current printable solids total 37.451 cm³ (about 46.4 g at 1.24 g/cm³, before paper, thread and adhesive). Combined hull-plus-keel displacement is 59.015 cm³ at z=0 and 66.835 cm³ at z=1 mm. Use the actual slicer mass and tank trim to set ballast; do not assume the nominal 9.28 g fill is the required load. |

Defended: use physical thread for the stays rather than fragile printed rigging, and retain the reduced sail. The 200 mm hull, small gear and keel can plausibly share the P2S plate, but the plate layout, mast orientation and material mass are not accepted until a real slice is inspected.

## Step 5 — v6 consultation on user feedback (wheels, mast/sail, teak, hatches)

User (screenshot of live v5): wheels face the wrong way; mast weird, not really carrying a paper sail;
shape good but lacks detail (teak flooring); hatch weird. Consulted independently:
**GPT-6.2 (engineering/printability)** and **Grok-4.7 (likeness)**, both given the six v5 review renders.

| # | Topic | GPT-6.2 | Grok-4.7 | Settlement (challenge → defend/accept) |
|---|---|---|---|---|
| 1 | Mast | 4.0×3.2 hollow box, thread lashings, no spreaders | 2.6×1.8 oval, truck z253, crane, swept spreaders z134/194 | **Compromise**: D-section 3.8×2.8 → 2.5×2.0 (stiff enough for paper + stays, near-scale look). Truck stays z231: a 256 mm spar does not fit the 256 mm bed with the plate. Flat aft face is the print face, so spreaders are unswept and there is no aft crane; masthead cap has a fore-aft thread hole. D-shaped heel keys the socket. |
| 2 | Boom | z44, 37 mm, gooseneck pin | z45, x24→−46, 1.6×1.1 | **Accept** height (both). Boom x24→−46, 1.8×2.2 (thread holes need ≥0.5 mm walls); lashed loop gooseneck on a mast saddle at z43 → swings freely. |
| 3 | Paper sail | 20–28 cm² triangles, lashings | ~70 cm² scale triangle, lashings, trial template | **Both agree lashings** through punched luff holes around the spar. Three templates (full/trial/breeze); render shows full; stability check chooses the recommended start sail. No jib (forestay only; optional rolled paper strip as furled genoa). |
| 4 | Wheels | X axis, 14.5 mm, binnacles in well | X axis, 14 mm, tilted, consoles on helm seats | **Accept X axis, 14 mm, navy, 3 spokes, printed flat with axle stub.** **Defend** binnacles in the wheel well tied to the bench ends: seat consoles put the rim 1 mm above the seat. No tilt keeps the axle bore horizontal-printable. |
| 5 | Teak | grooves only, no navy | navy caulk, sole/benches/helm/platform, white margin | **Accept Grok**: navy flush caulk 0.5 mm. Defend vs GPT purge concern: ink is already printed on those layers (names, ports, rail stripe, windows). v5 bench teak was buried under the deck → benches now real flat seats. Side decks stay white (both). |
| 6 | Hatches | framed 0.48 raised, lens −0.16, slider + garage + washboard | framed 0.7 raised, lens −0.4, delete x−15 sticker, companionway hood | **Framed hatches** raised 0.64 / lens −0.32 (between both). Keep foredeck, forward-roof and saloon hatch (defend: SO43 has saloon hatches; they are framed now). Companionway: smoked slider between rails, garage, navy washboards on the bulkhead. |
| 7 | Rudder trim | slotted stock under cover | delete rod; round tip | **Accept both**: tiller rod removed; Ø2 slotted stock in a navy deck-plate counterbore (friction trim); rudder tip rounded. |
| 8 | Extras | table, coachroof traveller, bow roller, winches; skip rails | non-skid border, genoa tracks, pulpit, 3 ports, cockpit traveller, no table | **Accept** bow roller, visible winches + clutches, genoa tracks, 3 oval ports, name at x≈72. **Defend** coachroof traveller and teak-top table (mid-boom sheet does not cross the cockpit). **Reject** printed pulpit/pushpit (0.9 mm rails snap in handling). |
| 9 | Bulb | refine mesh | "upswept tail looks like a clog" | **Bug found**: v5 NACA bulb was reversed (blunt end aft). Flip, droop ends to the section centre, finer mesh, larger shot cavity. |
| 10 | Fittings | forward fittings outside sheer | — | **Bug found**: v5 bow cleats at y±20 were outside the 15.3 mm half-beam; coaming winches were buried; stay-eye holes were blocked by their pads. All fixed (threadable teardrop padeyes). |

## Step 6 — v6 challenge/defend: engineering (GPT-6.2) and likeness (Opus), then verification

Both reviewers saw the eight v6 review renders, the generator and the exported meshes.

### GPT-6.2 engineering challenge

| # | Finding | Decision |
|---|---|---|
| 1 | Rudder blade crown intersects the hull bottom; Ø2 stock has no friction | **Accept.** Crown follows the hull underside with a 0.7 mm gap (checked 0.678 mm); bore Ø2.1 for friction trim. |
| 2 | Boom jaw binds at ~10° swing | **Accept.** Jaw replaced by a rounded tongue and gooseneck loop on a mast saddle; boom checked clear through ±45° (min gap 0.355 mm). Mainsheet hole gets a flat-sided boss. |
| 3 | Full 63 cm² main has little gust margin; ballast must come from sliced mass | **Accept.** Three paper mains (start 25 / medium 32 / full 63 cm²), start sail recommended; stability now uses the sliced on-board PLA mass. |
| 4 | Mast is a stayed spar, tip holes thin | **Accept.** Ø1.0 holes in larger spreader tips; tension stays only until taut; luff ties kept off the spreader roots. |
| 5 | Bulb posts index but do not retain; cup bottom is a small first layer | **Accept.** Tape for trials, epoxy the full land afterwards; cup printed opening-up, cap split-face down. |
| 6 | One-plate support/purge plan unverified | **Accept.** Real slice done (below). |
| 7 | Sub-line-width colour slivers (caulk ends, deck-plate ring, rail ink, bow flecks) | **Accept.** 0.65 mm white deck-plate ring, rail ink stripe reprofiled, tiny ink/teak islands removed (automated island check passes). |
| 8 | Wheel rim 0.144 mm from binnacle; round bore | **Accept.** Wheels moved aft (gap 0.401 mm), teardrop bores. |

### Opus likeness challenge

| # | Finding | Decision |
|---|---|---|
| 1 | Spreader tips sit inboard of the straight shroud line, so they brace nothing | **Accept.** Padeyes moved inboard to y ±18.5; spreaders now deflect the shrouds outward 3.15 / 2.65 mm; lower shrouds added. |
| 2 | 3-spoke wheels read as a car badge; blocky pedestals | **Accept.** Navy rim + white 6-spoke hub (two colours, printed flat); slim binnacles with navy instrument pods. |
| 3 | No headsail | **Accept (cosmetic).** Optional rolled paper furled genoa on the forestay; no working jib (would add lee helm). |
| 4 | Bare decks | **Accept.** 0.2 mm recessed non-skid panels with smooth margins, teak coachroof handrails, 8 mm teak-top table. |
| 5 | Rectangular rudder | **Accept.** Tapered spade 12 → 7.5 mm chord, 7° swept leading edge, R3 tip. |
| 6 | Blue rudder stock dot in the teak sole | **Accept.** Navy stock cap with a cross slot. |
| 7 | Renders lighter than the print colours | **Accept.** Render materials now equal the four print colours. |
| 8 | Pulpit/pushpit/lifelines | **Defend.** Not printed (0.7–0.9 mm rails snap in handling); documented as an optional wire/thread add-on. |

### Verification and physical-feasibility findings

- Independent verifier (Claude rubber-duck) re-checked all fixes on the v6c renders and exported meshes: **no material issues**.
- Slicing the real one-plate P2S job and the "on-board" mono plate (no support/purge) replaced estimated PLA with sliced mass.
- The first stability run showed the boat **stern-down**: the bulb moved forward (X_BULB −4.0 → −0.6); level-trim lead position now within 0.5 mm of the fill centroid.
- **Discrete packing finding:** a greedy lowest-first sphere deposition of 3 mm balls in the actual cup mesh showed the old cup held only **69–70 balls (≈11.2 g)** below the glue plane — the 62 % continuum estimate (18 g) was wrong for a narrow, tapered cup — while 13.1 g was needed. **Bulb enlarged** (L/half-width/half-height 58/7.5/7.2 → 64/8.6/8.0 mm, centre 1 mm lower). New result: needs **14.6 g = 92 balls**, holds **113 balls (18.1 g)**, ≈23 % spare.
- Final clearance checks: rudder gap 0.678 mm, cup∩cap 0 mm³, keel and mast clear of the hull, boom ≥0.355 mm through ±45°, wheel rim 0.401 mm, shroud deflection 3.15 / 2.65 mm, no tiny colour islands, all parts manifold.
- Final slice (P2S 0.4, 4 AMS colours): 12 h 26 min, 196.95 g incl. purge/support (white 84.9, blue 43.1, navy 53.0, teak 16.0 g), 297 colour changes, nothing outside the bed. On-board printed mass 46.06 g.
- **Bulb-enlargement challenge** (same verifier, scoped re-review): **no material issues** — bulb still proportionate to fin and hull; 113 vs 92 balls (21 spare ≈ 3.4 g); the 0.5 mm ballast-centroid offset moves the whole-boat CG only ~0.12 mm; 0.9 mm walls/floor intact, zero cup–cap interference; slice confirmed. Packing remains a simulation until a physical fill test.

## Step 7 — v7 consultation on user feedback (keel gap, float, paper sail, open stern, proportions, teak)

User questions: why is there a gap between keel and bulb; is the weight distribution right and will she float; how does a
paper sail go on and still float; open the swim platform properly or close it ("the step into the sea is weird"); check
proportions; is the deck-plan shape right; teak on the side decks and foredeck.

v7 changes: the fin runs down to the split plane with a fading root/tip contour; the bulb tail is rounded; the stern is open
with a full-width integral teak bathing platform, one tread step and a folding ladder in relief; the planform is fuller
forward with a blunter coachroof nose and a bow roller; sprung teak with king and margin planks on the side decks and
foredeck; one-piece 240 mm mast; an independent numpy hydrostatics check on the exported STLs (`hydro_check.py`). That
check found the v6 stability script had an inverted heel bisection and understated stability — corrected.

### Challenge verdicts

| User point | GPT-6.2-sol | Opus 5.5 |
|---|---|---|
| Keel–bulb gap | YES | YES |
| Float / weight distribution | PARTLY — label predictions vs tests; trim 0.7° bow-down with a level pour | PARTLY — move the bulb aft; tilted pours spill and coated balls don't roll |
| Paper sail | PARTLY — needs a rigging view | NO — needs a sheet; full sail only ≤ 1.5 m/s |
| Platform | PARTLY — ladder hinge pads | PARTLY — lost the reverse transom rake; ladder should lie fore-aft |
| Proportions | PARTLY — show the table | — |
| Deck plan | YES | YES |
| Teak | YES — tidy seam tails | YES — nib the bow planks |

### Decisions

| Proposal | Decision |
|---|---|
| Move the bulb aft so a level pour trims | **Accept.** X_BULB −0.6 → −13.0 (12.4 mm aft). |
| Tilted-pour instruction | **Reject.** Replaced by the bulb move; pour level. |
| Mainsheet + rigging diagram; start sail first, full only < 1.5 m/s | **Accept.** Annotated rigging sheet and PDF text. |
| Label calculation vs physical test; verify the slice | **Accept.** Afloat sheet marked "calculated"; real slice + per-object G-code mass. |
| Reverse transom rake | **Accept.** ~8° (1.6 mm over 11.5 mm), padeyes kept on deck. |
| Folding ladder fore-aft with hinge pads | **Accept.** |
| Nibbed bow planks / seam tails | **Accept.** Seams stop 1.2 mm short and close square; runs < 4 mm dropped. |
| Reframe views (masthead cut) | **Accept.** |
| Flat bulb bottom, rudder gap | **Skip** (both reviewers). |
| Widen the transom walk-through; real-boat collage | **Skip.** Collage showed a different model; walk-through already clears. |

### v7b implementation findings

- `upper ∩ (teak − seams)` returned **empty** from the exact boolean solver (teak volume 0 cm³). Fixed by
  `(upper ∩ teak) − seams` with a kept seam tool, non-coplanar nib seams and a teak-volume assert (now 2.20 cm³).
- Two 0.003 mm ink slivers at the coachroof nose → export-time crumb remover (components < 0.05 × 0.1 mm); checks clean.
- Re-slice (P2S 0.16 mm): 12 h 58 min, 235 layers, 320 colour changes; on-board PLA from per-object G-code **45.83 g**.
- Hydro (sliced masses, level pour): all-up 63.97 g with **100 × 3 mm balls (16.0 g)**; trim **0.10° bow-down**
  (was 0.70°); GM 19.0 mm; AVS 141°; deck edge immerses at 31°, cockpit sill at 130°; reserve buoyancy 165 g.
- Stability: CE ahead of CLR 4.0 mm (full) / 12.2 mm (start); heel at 1.5 m/s 6.8° (full) / 2.1° (start).

## Step 7b — defend round on v7b (GPT-6.2-sol and Opus 5.5), fixes shipped as v7c

| Reviewer | Verdict | Fix applied in v7c |
|---|---|---|
| GPT-6.2-sol | Accept keel joint, trim, platform, proportions, deck plan | — |
| GPT-6.2-sol | FIX: teak nib returns spur past the curved coachroof margin seam | `td_lim(x)` follows the true curved margin-seam centreline; nibs end 0.05 mm inside it (spurs gone in the foredeck close-up). |
| GPT-6.2-sol | FIX: rigging sheet must label FULL and explain start/medium; "cockpit eye" is wrong | "FULL SAIL SHOWN" heading, HEAD callout for full vs start/medium, "coachroof eye". |
| GPT-6.2-sol | FIX (blocking): afloat claims overstated | "Sealed hull self-rights to 141° (AVS); a flooded cockpit past 130° is not modelled"; 165 g is labelled full-submersion reserve; caption says the hull sits 0.03 mm deeper; tub leak check added to the physical test. |
| Opus 5.5 | Accept all; paper sail and platform now YES | — |
| Opus 5.5 | FIX: "cockpit eye" → coachroof/traveller eye; header v7 → v7b | Applied. |
| Opus 5.5 | FIX: stability used stale part masses | `stability_v7.py` reads per-object G-code masses via `SLICE_MASS`. |

v7c verification: checks unchanged (no tiny islands, all gaps OK), slice identical (on-board PLA 45.83 g), hydro unchanged
(trim 0.10°, GM 19 mm, AVS 141°), heel slightly lower with corrected masses (full sail 6.7° at 1.5 m/s).

## Step 7d — anchor, transom name and display stand (user requests), challenge round

User asked for an anchor on the bow, the name repeated on the port transom face, and a minimalist table stand.
v7d added a navy delta anchor stowed on the bow roller (printed in the white upper hull, no glue, no new supports:
G-code support moves identical to v7c), "Margaret" inlaid 0.4 mm into the port transom face, and a one-colour stand
(base plank + two cradles whose notches are cut from the real hull sections, 0.3 mm clearance, bulb 3 mm clear of the base).

| Reviewer | Finding | Decision |
|---|---|---|
| GPT-6.2-sol | BLOCKER: the transom name slices into scattered navy | Accepted → Steps 7e/7f |
| GPT-6.2-sol | Chamfer the cradle notch rims 0.4 mm | Accepted (v7e stand) |
| Opus 5.5 | Same transom blocker; strokes 0.32–0.44 mm; gate: no zero-navy layer, ≥1.5 mm navy per layer; fallback 0.8 mm depth | Accepted; gate adopted and tightened |
| Opus 5.5 | Anchor prints well (navy continuous bed z 12.2–19.9) and reads as an anchor | Accepted |
| Opus 5.5 | Stand tips at 30.9° but the boat rolls out of the cradle first; don't widen the base, tell the owner to rig off the stand | Accepted (sheet + README note) |

## Step 7e — first name fix failed the per-layer gate

v7e enlarged the name (cap 3.3 → 3.9) and deepened it to 0.6 mm. Checks and LOA unchanged, but the per-layer navy scan
of the real slice still FAILED: zero-navy layers at bed z 6.28 and 8.36, median 1.09 mm of navy per layer (bow control:
12.87 mm, no zeros). The per-glyph gate missed M 20/34, r 8/11 and g 13/20 strokes, with runs up to 8 layers.

Measured strokes: transom 0.5–0.6 mm wide × 0.62 mm deep; bow 0.6 × 0.45. A ray-cast ruled out ink/white overlap.

## Step 7f — coupon diagnosis, fix, challenge/defend, G-code gates

**Coupon experiment** (same P2S profile, 1.06 mm white wall with the inlaid name, sliced in < 2 s each):

| Variant | Zero-navy layers | Median navy/layer | Result |
|---|---:|---:|---|
| A: 0.6 mm (v7e) | 3 | 1.0 mm | Illegible, reproduces the bug |
| E: A, face rotated 90° | — | same as A | Orientation is not the cause |
| B: 0.8 mm deep | 0 | 6.9 mm | Legible |
| C: through-wall | 0 | 9.5 mm | Legible |
| D/F: Blender text offset bolding | — | — | Corrupts glyphs, rejected |
| G: 0.8 mm + 1.66 mm wall | 0 | 6.9 mm | Same as B |

**Diagnosis:** strokes about as deep as they are wide give Arachne a near-square cross-section per layer and its
medial-axis beads collapse. Depth ≥ 0.8 mm fixes it; wall thickness behind does not matter.

**Fix (v7f):** inlay 0.8 mm, plus a white backing pad unioned inside the transom (0.6 mm beyond the inner face,
chamfered underside so it prints without support). Through-wall was rejected: it would put a navy/white seam through a
wall that the port transom corner dips ~5 mm under at 30° heel. As built: ink depth 0.828 mm, white behind the ink
0.848 mm everywhere, ≥ 5.73 mm void behind; `Upper_white` stays one shell; all other checks identical to v7e.

| Reviewer | Challenge | Defence / decision |
|---|---|---|
| GPT-6.2-sol | Ship after fixes; the pad chamfer may eat the backing under the lowest letters | Refuted: the ramp runs name_min−1.5 → name_min−0.5; measured white behind the ink is 0.848 mm everywhere |
| Opus 5.5 | Ship after fixes; the pad might be coplanar with the wall | Already handled: the pad starts 0.12 mm inside the wall; union is manifold, one shell |
| Both | Add G-code gates: per-glyph stroke continuity (no glyph missing strokes > 2 consecutive layers) and continuous white behind the ink (gaps < 0.1 mm) | Accepted: `coupon/transom_gates.py`, `coupon/namecheck.py` |
| Opus 5.5 | Small counters (a, e, g) may fill in | Accepted as cosmetic; the preview reads cleanly |

**Gate results on the real v7f plate slice:**
- `transom_gates.py`: **PASS**. All 8 glyphs (M a r g a r e t), 0 missed strokes, max run 0; white-behind gap 0.00 mm in
  all 17 layers. (v7e on the same gate: FAIL.) The white gate measures across the letters' own extent, not the whole
  pad, which first produced false 0.39 mm "gaps" beyond the last letter.
- `namecheck.py`: transom 17/17 layers with navy, no zero layers, median 6.49 mm; bow 19/19, median 12.87 mm.
  The face-on G-code preview reads "Margaret".

**Stand (v7f):** 0.4 mm rim chamfer, 0 non-manifold edges, 35.69 cm³, min hull clearance 0.28 mm, 55 min 5 s / 30.87 g.

**v7f pipeline:** slice 13 h 3 m 7 s model time (235 layers, 207.8 g total), on-board PLA 45.91 g (+0.05 g pad),
all-up 64.0 g with 100 balls, trim 0.10° bow-down, GM 19.1 mm, AVS 141°, heel unchanged.

## Step 8 — one-wall stand, rig/sail purpose, optional printed display sail

User: "can the stand be even more simple? with one wall?" and "print the rigging and the sail? alternatively … water
worthy and can sail under wind". Proposal: replace the two-cradle stand with a base plank and ONE wall; keep thread
stays and paper sails for sailing; add an optional printed display mainsail. Two independent challengers.

| Reviewer | Challenge | Defence / decision |
|---|---|---|
| GPT-6.2-sol | One wall cannot hold a boat; where does the weight go? | Redesigned: she stands on her keel. The bulb's printed flat sits in a 0.8 mm locating pocket (0.4 mm offset); the wall (x 23.4, 4 mm) only stops roll and nose-down |
| GPT-6.2-sol | Standing on the bulb loads the glue joint in tension | Refuted from `build_v7.py`: posts stop 0.3 mm short of the hole bottoms, 0.2 mm radial clearance, so the cup rim and split face bear the load in compression. Tape/glue the cup before standing her |
| GPT-6.2-sol | Rocking on a narrow keel flat | Accepted: G margins 18.4 mm aft / 11.3 mm fore of the flat; nose-down blocked by the wall |
| Opus 5.5 | A nose-up rock tips over the plank's aft edge | Accepted: plank extended under the whole bulb tail (+2 mm); the tail lands after 12.3°; nose-up tip now computed about the tail tip: 47.8° full lead / 40.3° no lead |
| Opus 5.5 | Hull might land on the notch floor instead of the keel carrying it | Accepted: notch floor relieved 1 mm over \|y\| ≤ 8 with a compact smooth-max blend (a plain one widened the notch 0.15 mm); floor now 1.3 mm below the keel |
| Opus 5.5 | Drop the pocket for simplicity? | Kept: its forward rim catches the bulb nose slope and is the only aft stop |
| Opus 5.5 | Paper template: labels inside the cut line; plain sail looks toy-like | Accepted: labels moved below the foot; grey cloth detail (seams, battens, tabling, patches); matte tape |
| Opus 5.5 | Printed sail: 0.6 mm sheet is thick, corners curl | Accepted as display-only: 0.52 mm + 0.16/0.32 mm relief, Ø10 × 0.2 mm mouse ears at head/tack/clew on the bed copy only, peel when cool |
| Both | Printed stays or genoa | Rejected: ≥ 1 mm = 66 mm wire at scale, can't be tensioned, fragile |
| Both | Explain the rig plainly | Accepted: README leads with "printed spars; thread = wire, holds the mast; paper sails 0.5 g so she sails; printed sail 4.5 g = display only" |

**Display sail as built:** 0 non-manifold edges (6 found first: patches/battens now clipped to an inset outline, hole
polygons rotated half a step), 66.9 cm², 4.5 g (slice 4.51 g, 9 m 8 s), ears 0.04 g. Afloat it would raise G ≈ 6.9 mm
and cut GM 19.1 → ≈ 12 mm: display only.

**Stand as built:** 83.2 × 56 × 55.7 mm, 24.85 cm³, 0 non-manifold edges, min notch clearance 0.288 mm, notch floor
1.3 mm below the keel, pocket gap ≥ 0.72 mm, slice 43 m 37 s / 20.13 g (two-cradle stand: 55 m / 30.9 g).
Tipping (full lead / no lead / display sail): nose-up 47.8 / 40.3 / 43.6°, assembly sideways 33.8 / 29.3 / 30.5°,
forward 39.4 / 33.3 / 35.8°, aft 49.5 / 45.2 / 45.8°.

## Step 9 — raked-wall stand: deliberation across three models, then built and re-challenged

User: "I was thinking of the stand that has a wall with an angle — deliberate with different models and decide which
stand would suit here better and if you decide — you can revert to the original design." Read as one wall leaning
fore-and-aft in side view (other readings, e.g. diagonal in plan, were put to the judges too). Options: A = original
two-cradle stand (120 × 50 mm), B = upright one-wall stand (Step 8), C1 = one wall raked top-forward, C2 = raked aft,
C3 = diagonal in plan. Three independent judges on different models got the same brief, renders and measurements
(fin leading edge sweeps 11.1°, rudder 8.2°, bulb nose x 16.4).

**Round 1 — pick one option**

| Judge | Pick | Main argument | Borrow |
|---|---|---|---|
| GPT-6.2-sol | C1 at 11.1° | Repeats the fin rake in profile; A's aft cradle hides the rudder, B reads as a bracket; 20–25° grows the plank toward A | A's smooth saddle rim (0.4 mm chamfered lead-ins) — already in B/C |
| Opus 5.5 | C1 at 11.1° | Exactly parallel to the fin reads as deliberate (a third blade); C2 implies a buttress and pinches the fin root; C3 skews the notch | A's "nothing overhangs the base": run the plank under the wall top |
| Grok 4.7 | C1 at 15° | 11° might still look vertical; keep B's keel-bears-weight load path | Appendages are not landing gear: check the rudder on a nose-up rock |

Not revert to A: all three judged two cradles heavier, longer (120 mm) and hiding the rudder. C2 was also killed by
measurement: a −15° prototype put the bulb through the wall on lift-off (226 / 694 vertex hits at 20 / 30 mm).

**Built.** `stand_v7.py` gained `STAND_RAKE_DEG`: the wall is a sheared slab (4 mm square to its faces), the notch is the
vertical-sweep hull + fin + bulb envelope sampled across the inclined slab at every height, and two new gates stop the
build: (1) 13.5k hull / fin / bulb / rudder vertices raised straight up 0–30 mm must never be inside the wall (ray-parity
point-in-solid; a first nearest-normal test gave false hits), (2) the wall must stay ≥ 2 mm from the fin and bulb.
Prototypes 0 / 11 / 11.1 / 15 / 20 / −15° were built and rendered (new port-profile render `stand-5`).

**Round 2 — challenge/defend on the built result**

| Reviewer | Challenge | Defence / decision |
|---|---|---|
| GPT-6.2-sol | Plank 54 mm wide (rounding) costs sideways margin; the bow lead past the wall top is conspicuous | Accepted: width back to 56 mm (`BASE_W_MIN`), lead past the wall top 6 → 3 mm (`FRONT_MARGIN`): 92.3 → 89.3 mm |
| GPT-6.2-sol | Tail-pivot tip angles are calculations, not measured table-tilt margins | Accepted: sheet and README now say "calculated", with a tilted-board check after printing |
| GPT-6.2-sol / Opus 5.5 | Fore-face gap 0.94 mm (B 0.81): cut each face to its own envelope? | Kept: +0.13 mm on B, near FDM tolerance; per-face lofting undercuts the curved hull and would need the lift-off audit redone |
| Opus 5.5 | Rake nearly vanishes in the 3/4 view | Accepted as a presentation point: the sheet adds the port profile as a full-width panel |
| Opus 5.5 | 1.5 mm root fillet against knocks | Declined: the keel carries the load, the wall only stops roll; root is 26 mm wide × 4 mm on a 4 mm plank |
| Grok 4.7 | 15° instead of 11.1° | Built both. 15° opens a diverging 5 → 8 mm V to the fin and has 1 vertex inside the wall at rest (gate fails); 11.1° keeps 5.0 mm at every height and 0 hits. Grok conceded: "Ship 11.1°" |
| Grok 4.7 | Rudder must not land on a nose-up rock | Checked: at the 12.3° tail landing the rudder tip is still ≈ 21 mm above the table |

**Decision: C1, one wall raked 11.1° forward, parallel to the fin leading edge (3 / 3 judges).**

**Stand as built:** 89.3 × 56 × 55.7 mm, 26.09 cm³, 0 non-manifold edges; wall foot x 22.35, top x 32.48; horizontal
gap to the fin and bulb 5.0 mm at every height (3D minimum 4.91 mm); min notch clearance 0.286 mm, visible face gap
0.42 aft / 0.94 fore; notch floor 1.3 mm below the keel; lift-off 0 hits at every step; slice 44 m 47 s / 20.84 g,
no supports. Calculated tipping (full lead / no lead / display sail): nose-up 47.8 / 40.3 / 43.6°, assembly sideways
34.1 / 29.6 / 30.7°, forward 43.8 / 37.7 / 40.1° (upright wall: 39.4 / 33.3 / 35.8°), aft 50.1 / 46.0 / 46.5°.

## Step 10 — swan-neck stand, printed rig, sail markings, separate-looking anchor (v7g)

User: "I was thinking of that kind of a stand [an airplane-model stand: low base, one curved neck] but without a pin
that would go into the model, it should still hold it and the stand must be way lighter and simpler. If we have sails
that we print they should look like real sails and have markings — numbers and codes? Anchor looks like it is a part
of the body of a boat. It should be part of it but look like it is a separate entity. What about the rigging? If we
have it — it should be printable or not to have it at all."

The same three reviewers (GPT-6.2-sol, Opus 5.5, Grok 4.7) got one brief covering all four topics. Their decisions were
synthesised, built as v7g, and the built result went back to all three for a second, challenge/defend round.

**Round 1 — design decisions**

| Topic | Decision | Rejected / why |
|---|---|---|
| Stand | One neck rising **ahead** of the bulb, a fork under the hull: two pads follow the hull bottom either side of the fin and carry her; the fin sits in the slot with 0.4 mm per side; a low saddle under the bulb tail stops her sliding aft; thin bevelled oval base | Grok's aft neck (as in the reference photo): it must arc ~50 mm forward over the bulb while rising ~45 mm, a > 60° overhang. Friction-only hold (all three). GPT's separate keeper (an extra part). A sill on the cheek tops (it would cut into the hull) |
| Rig | Print it: mast + spreaders + cap and lower shrouds as one flat frame, navy, feet dropping into funnel pockets in deck chainplate blocks. A printed furled genoa (display only) hooks over the masthead and drops into a stemhead pocket. Thread holes removed | Backstay (all three): a split Y does not fit the plate, and the masthead is too thin for a clip. A thread rig (the user asked for printable or none) |
| Markings | Sail number **MGT 43** (code for Margaret, not a country), 6.8 mm capitals = RRS 450 mm at 1:66, one set per face, starboard higher; a symmetric two-wave insignia at the head; two reef rows. Same marks on the paper PDF. `SAIL_CODE` / `SAIL_NO` override | Grok's full-thickness number in one place (reads backwards from one side). Telltales, draft stripes, sailmaker logo (clutter at 1:66). A display genoa (the furler is the genoa) |
| Anchor | Real daylight: a 1.0 mm shank between the cheeks with 0.65 mm each side; it touches only the roller and a deck chock via a D-ring shackle; the delta fluke hangs off the stem with a shadow gap and touches only at a toe pad (which starts its print); the crown stands proud | A chain (below the feature floor, and it would collide with the furler foot) |

**Built (v7g).**
- `stand_neck.py` (new) builds the stand from the boat's own geometry and stops if any gate fails: fin-slot and saddle clearances, a lift-off path checked at 615,839 vertex positions, and overhangs ≤ 50°.
- `build_v7.py` adds the shroud frame (1.0 × 0.6 mm strips on the mast's aft print face, one part with the mast), the chainplate blocks and pockets, the stemhead block, the furler and the new anchor. `check_v7.py` measures the furler hook, the drum tab and the shroud feet.
- `sail_marks.py` (new) is shared by `display_sail.py` (navy inlay on the port bed face, 0.16 mm navy relief on starboard, full-thickness insignia) and `presentation_v7.py` (paper PDF).
- Hydro and stability re-run with the frame on board and the furler ashore.

**Round 2 — challenge/defend on the built result**

| Reviewer | Challenge | Defence / decision |
|---|---|---|
| All three | Furler hook clearance 0.126 mm measured (0.15 nominal) between two separately printed flat parts is an interference fit; the 1.0 mm hook stock would crack | **Accepted (must-fix).** Targets: GPT/Opus ≥ 0.25–0.30, Grok ≈ 0.35 and ≤ 0.45 so it still stays on. `HOOK_CLR` 0.15 → 0.375: **0.358 mm measured** |
| Opus 5.5 | Shroud foot to chainplate pocket only 0.155 mm | Accepted: pocket seat +0.1 mm in x, **0.207 mm measured** |
| Grok 4.7 (must-fix), GPT / Opus (nice) | Cut the fork cheeks back so ~8 mm of the fin's leading edge shows below the hull | Challenged by measurement: from the pad lip (x −9.0, z −13.4) to the fin leading edge (x ≈ +5, z ≈ −20) is a **65° overhang** against the 50° rule (stand max 48°). Options put back: (a) keep, (b) a 50° taper that gains ~2 mm and spends the last 2° of margin, (c) shorter pads with G behind them and a zero-gap seat on the glued bulb. **Opus and Grok both chose (a) and withdrew the item**: the hidden fin root is the price of a support-free stand |
| Opus 5.5 / GPT-6.2-sol | A white seam runs through the starboard "43" | Accepted: seams and relief stop 0.6 mm short of each number line (a seam-free panel like a sail-number patch) |
| Opus 5.5 | The views show a blank paper main, so the markings are invisible on the main sheet | Accepted: the paper-sail preview carries the marks (render-only, not printed) |
| Grok 4.7 | The 0.16 mm starboard relief may print faint | Deferred to the proof print: go to 0.24 mm (one more layer) if it is faint; noted in the README |
| GPT-6.2-sol | Check the first anchor-fluke layers in the slice | Defended on geometry: the fluke starts on its toe pad on the stem; Opus and Grok judged it printable |
| All three | Stand load path, neck stress (≈ 0.6–2 MPa against ≥ 15 MPa for PLA), base thickness, saddle (not a pin), marking layout, anchor separation | Defended, no change. The round-1 T3 note had the paper's mirrored side the wrong way round; the build (port lower and normal, starboard higher and mirrored on the paper) is the one all three confirmed |

**As built (v7g).**
- **Boat plate:** 10 parts, 19 colour volumes; 13 h 06 min model time; 209.0 g filament (80.7 / 43.4 / 55.9 / 29.0 g).
- **Mass and float:** 47.0 g printed, 46.4 g on board (the 0.6 g furler stays ashore); 98 balls (15.7 g), all-up 63.9 g. GM 18.7 mm (v7f 19.1); GZ 3.2 / 6.0 / 8.2 mm at 10 / 20 / 30°; AVS 140°.
- **Fits:** furler hook 0.358 mm, shroud feet 0.207 mm, furler drum tab 0.2 mm; no overlaps.
- **Stand:** 74 × 60 × 48 mm, 8.67 cm³, no supports (max overhang 48°); 29 m 28 s, 10.1 g (the raked-wall stand was 44 m 47 s, 20.84 g). G is 5.3 / 7.1 / 5.4 mm inside the aft end of the pads; the assembly tips sideways at 32 / 27 / 29° and forward at 36 / 29 / 32° (full lead / no lead / display sail).
- **Display sail:** 4.53 g, 0 non-manifold edges, 0 mm³ white/navy overlap; 20 m 5 s.

## Step 11 — outboard chainplates, printable railings, visible cleats, a stand from aft (v7h)

User:
* "I think the rigging goes closer from the side of the boat and not closer to the middle."
* "Can we think of simple and able to print railings on the boat perimeter?"
* "We do not have cleats — those will be hard to print but maybe you can think of something."
* "The stand should be from the back of the ship, holding it same way as now, raising from between the steering and
  the kiel and raising the ship up."

The same three reviewers (GPT-6.2-sol, Opus 5.5, Grok 4.7) got one brief for T1–T3 and one for T4. Their decisions
were synthesised and built as v7h, and the built result went back to all three for a second, challenge/defend round.
The full tables are in the session's `review11/DECISIONS.md`. A summary:

**Round 1 — design decisions**

| Topic | Decision | Rejected / why |
|---|---|---|
| T1 Chainplates | All three agreed with the user. The feet at ±17.6 landed beside the coachroof (58 % of the half-beam); real SO43 chainplates sit at ~85–90 %. Moved to **±26.0** (86 %), inboard of the rail line, on a 3.6 × 3.2 pad. The spreaders were widened to 24.0 / 14.5 mm half-span so the cap shroud still bends visibly at the lower tip. The lower spreader is thicker and tapered. | Grok's "keep the short spreaders" (the cap shroud would run straight to the deck, unlike the real rig). Opus's 26 mm lower spreader (no visible bend left) |
| T2 Railings | Flat-printed **navy fences**, 0.68 mm thick: pulpit 10.5, lifelines 9.2 (mid rail 4.7), pushpit 10.0 mm above the deck. They are laid out from the final deck-edge curve, so each strip bends elastically rather than creasing. Each post has a 0.7 mm tab that drops into a slotted pocket in a navy stanchion pad (no hole into the hull), with the slots lengthened for print shrink. The pulpit is split at the bow. Separate transom returns. The rails print on the boat plate. | Rails printed in place on the hull (one snapped post would scrap a 13 h print). Thread lifelines (they sag). Posts only (no lifelines). A closed pulpit bar (fragile, and it would clash with the furler and anchor) |
| T3 Cleats | Root cause: six white 0.9 mm cleats stood on white cut-outs in the teak, so they were invisible. Replaced by **integrated navy horn cleats**, 4.2 × 1.2 mm, with all undersides at 45° or less and daylight under the horns. Bow (79, ±9), midship (−30), stern (−78.6, ±23.5), clear of the rails. | Loose printed cleats (tiny parts). Fairleads and chocks (clutter at 1:66) |
| T4 Stand from aft | The neck root moves aft of the bulb (x −60…−53.5), rises vertically, then leans about 50° forward into a fork that is **closed aft** behind the keel's trailing edge. A saddle under the **bulb nose** is the forward lock. Tree supports go under the fork head only. The egg base is wider under her centre of gravity. To exit: lift, slide forward, lift off. | Opus's support-free wedge (its lowest corner would print in mid-air at (−23.4, −40.5)). Grok's 1.2 mm bead on the pad tips (it rides on the hull or locks nothing) |

**Built (v7h), and what the build itself changed**

* A narrow fork cannot release the boat: after the slide the bulb sits under the prongs, and sliding far enough to
  clear it drives the rudder into the neck. The slot now flares forward to the bulb's plan outline, shifted by the
  slide, so after lift 3 / slide 29 the fin and bulb pass up through the open V. The rear 7 mm keeps the 0.4 mm fin
  fit. Lift-off checked at 729,497 vertex positions: **0 hits**; the rudder ends 2.8 mm from the neck.
* The neck was widened to 8 mm so every unsupported face is ≤ 49.2°. A 0.05 mm inset splits the coplanar faces, giving
  0 non-manifold edges.
* `check_v7.py` measures every railing tab (0.15 mm per side, none buried), the fence gap above the pads and the
  distance to the rig and wheels. The rail print sheet must be manifold, or the build stops.

**Round 2 — challenge/defend on the built result**

| Reviewer | Challenge | Defence / decision |
|---|---|---|
| Grok 4.7 | — | Everything accepted |
| GPT-6.2-sol | The cleat horns read as wedges | **Accepted:** 0.48 mm of straight waist added under the horns (top 2.24 → 2.72 mm) |
| Opus 5.5 | A stray post rises above the pushpit in profile | **Rejected by measurement:** it is the port wheel rim seen edge-on (top z 29.75 at x −74.5). The return panel's top, 26.21, is level with the pushpit corner (26.2). Opus withdrew it |
| Opus 5.5 | Double posts at each stern corner | **Accepted, stronger variant:** the return's outer leg is now a post without a tab. It stands on the side fence's corner pad, flush with the fence's outer face, and is glued along its full height to the corner post's aft face. It reads as one post |
| Opus 5.5 | Midship cleats sit 0.7 mm under the fence | **Accepted:** moved from y ±27.2 to ±25.0, inboard of the fence |
| Opus 5.5 | Bow cleats are hidden by a pulpit leg; move them to x 75 | **Rejected:** the cleat (x 76.9–81.1) is clear of the post at 82, so the overlap is only the camera angle. At 75 it would sit next to the post at 72. Opus withdrew it |
| Opus 5.5 | Stand base 1.8 → 1.4 mm | **Accepted** (the user asked for "way lighter"): 13.7 → 11.0 g finished |
| Opus 5.5 | Report the roll angle in the fork | Answered: the bulb is about 40 mm below the pads and the nose saddle is 0.443 mm clear, so roll stops at about 0.6°. G sits above the pad edges, so the boat rights itself. No change |

Opus confirmed all six items on the rebuilt close-ups, and round 2 is closed.

**As built (v7h)**
- **Boat plate:** 11 parts, 20 colour volumes, 235 layers.
  - 13 h 12 min model time.
  - 209.8 g filament (80.7 / 43.4 / 56.7 / 29.0 g).
- **Mass and float:**
  - 47.9 g printed, 47.3 g on board (the furler stays ashore); 93 balls (14.9 g); all-up 63.9 g.
  - GM 17.7 mm (v7g 18.7); GZ 3.0 / 5.6 / 7.7 mm at 10 / 20 / 30°; AVS 137°.
- **Fits:**
  - railing tabs 0.15 mm per side; fences 2.26 mm above their pads and 1.9 mm from the rig and wheels;
  - shroud feet 0.207 mm; furler hook 0.358 mm; no overlaps.
- **Names:** transom gate PASS; transom 17/17 and bow 19/19 layers carry navy.
- **Stand:**
  - 96.5 × 63.8 × 54.1 mm, base 1.4 mm.
  - 44 m 5 s, 12.7 g with tree supports under the fork head, 11.0 g finished.
  - G is 8.5 / 6.8 / 8.4 mm inside the front end of the pads. The assembly tips sideways at 31 / 27 / 28° and forward at 33 / 28 / 30° (full lead / no lead / display sail).

## Step 12 — railings removed, stand chock removed, stand calculations (v7i)

**User:** "the railing are terrible, if you cannot do better - remove them"; about the bulb-nose saddle on the stand, "do
we need this part? remove it"; and "I hope the stand can keep the construction, hope you did the calculations".

**Round 1, the brief (`review12/BRIEF.md` in the session): Q1 improve or remove the railings; Q2 the stand without the chock**

| Reviewer | Q1 railings | Q2 stand without the chock |
|---|---|---|
| GPT-6.2-sol | **Remove** posts, pads and slots; keep the toe rail, chainplates and cleats | **Accept.** Check on the print that she does not creep at 10° nose-down, with and without lead; lift her off before moving the stand |
| Opus 5.5 | **Remove** everything, including the pads and the gluing step | **Accept.** Friction holds her to about 16°, or against a push of about 0.19 N; update the lift-off note |
| Grok 4.7 | **Remove** everything; the toe rail stays | **Fix:** a 1.2 mm nib on each prong at x 5.6–7.0 |

**Decisions**
* **Railings removed** (3/3). At 1:66 a stanchion is 0.38 mm and a lifeline 0.09 mm. The thinnest post a 0.4 mm nozzle
  prints reliably (1.0 mm) reads as a fence, not wire, so no printable railing can look right. The posts, 20 deck pads
  and pockets, the print strip and the gluing step are gone (`RAILINGS = False` in `build_v7.py`). The teak runs
  unbroken, and the toe rail, cleats and chainplates carry the deck edge.
* **Chock removed** (2 accept). **Grok's nib was rejected on geometry:** at x 5.6–7 the slot flares to 7.7 mm
  half-width so the bulb can pass up through it on lift-off, and the fin there is about 2 mm thick. A 1.2 mm nib never
  touches the fin, and one large enough to catch it blocks the bulb's exit. **Longer prongs** (tips at x 12 instead of
  x 5) were tried and **reverted**: the lift-off sweep hit at slide 8 / lift 3, and the gain was small.
* **Forward hold, calculated** (`stand.json` → `forward_hold`). The hull bottom's low point lies inside the pad span,
  so the pads are a cradle. Moving forward she must rise 0.13 mm by 9.5 mm of slide: 1.37° at rest, 0.78° on average.
  The brief's claim that she *drops* 0.2 mm was wrong, and was corrected by measurement before the build. With μ 0.3,
  using the average slope (conservative), she holds to **17.5° of forward tilt** and needs a **0.20 N** push to start
  sliding. G stays over the pads for 8.45 mm with full lead and 6.65 mm without.
* **Neck strength, calculated** (`stand_strength.py` → `stand_strength.json`). Every 2 mm, `Stand.stl` is cut on a
  horizontal print-layer plane. For each section the script computes area, centroid and I by Green's theorem, then the
  layer-plane stress σ = M·c/I − W/A with M = W·(G.x − x_c). Worst layer, z −39.4 at the start of the lean: **1.42 MPa**
  with the display sail (68 g). That gives SF **10.6** static and **3.5** under a 3 g knock, against a conservative
  15 MPa interlayer strength. The load point sags 0.58 mm, and 1.17 mm allowing a 2× creep factor. Paper sail: 1.33 MPa,
  SF 11.3.

**Round 2 — challenge/defend on the built v7i**

| Reviewer | Verdict | Challenge | Defence / decision |
|---|---|---|---|
| GPT-6.2-sol | ACCEPT | 0.13 mm over 10 mm averages 0.74°, not 1.37°; say where 1.37° applies before quoting 18.1° | **Accepted:** 1.37° is the local slope at rest. The hold and push now use the average slope to the cradle rim (0.78°): 18.1° → **17.5°**, 0.203 → 0.197 N. Both slopes are in `stand.json` |
| Grok 4.7 | ACCEPT | Same slope point; "hold still about 17°" | Same fix. Grok also confirmed the nib rejection: "do not put the peg back" |
| Opus 5.5 | ACCEPT | Nothing material; lead 93 → 98 balls after the rails came off is consistent | — |

**As built (v7i)**
- **Boat plate:** 10 parts, 19 colour volumes, 235 layers, 322 colour changes; 13 h 6 min model time (13 h 13 min total);
  209.1 g filament (80.7 / 43.4 / 56.0 / 29.0 g).
- **Mass and float:**
  - 47.1 g printed, 46.5 g on board; 98 balls (15.7 g); all-up 64.0 g; trim 0.12° bow-down.
  - GM 18.6 mm (v7h 17.7); GZ 3.2 / 5.9 / 8.1 mm at 10 / 20 / 30°; AVS 140°; heel 12° at 2 m/s with the full sail.
- **Checks:** `checks.json` unchanged apart from `railings: removed in rev 12` (navy deck-ink islands 106 → 104).
  Transom gate PASS; transom 17/17 and bow 19/19 layers carry navy.
- **Stand:**
  - 96.5 × 63.8 × 54.1 mm, 9.19 cm³; 0 non-manifold edges; steepest unsupported face 49.2°.
  - 43 m 16 s, 12.3 g with tree supports, 10.6 g finished.
  - Lift-off 0 hits in 729,497 vertex checks. Fin-to-slot 0.40 mm, bulb-to-neck 3.68 mm, fin TE to stop 0.46 mm.
  - Tipping at 31 / 27 / 28° sideways, 33 / 28 / 30° forward.
- **Physical checks still to do:** the base sits flat; at 10° nose-down she does not creep (with and without lead).
  Lift her off before moving the stand.

## Step 13 — thicker underwater hull (v7j)

**User:** "I printed two parts of the boat - the bottom blue part comes out too thin in plastic", and "how do those parts
come together? the bottom and the upper part of the body? using filament?"

**Diagnosis.** The lower hull wall was 0.85 mm everywhere below the 1.7 mm seam land, only two 0.42 mm wall lines.
Assumption (stated to the user): "the bottom blue part" means this shell, not the bulb or fin box.

**Decision: 1.2 mm below the waterline.**
- The change is one `BUMPS` entry in `build_v7.py` (`BOTTOM_WALL = 1.2`). It fades out into the seam land between
  z 0.4 and 1.3.
- The outer hull is unchanged, so hydrostatics and looks are the same.
- **Rejected alternatives:**
  - **1.0 mm:** still prints as two lines, so it gains almost nothing (Opus).
  - **Thicker still:** each extra 0.1 mm costs about 6–7 balls of lead (0.35 mm cost 23).
  - **Slicer-only (more wall loops):** cannot thicken a 0.85 mm wall, because the geometry is the limit.
  - **Thicker topsides as well:** would change the already-printed upper half, so it was offered, not done.

**Boolean fix in the pipeline.** Splitting the new lower half into blue, white and navy bands with Blender's exact
solver silently returned empty bands (Lower_ink 0 cm³). The fault sat near the aft seam lug.
- **Tried and rejected:**
  - `use_self`: left 6 non-manifold edges;
  - triangulating first;
  - dissolving degenerate faces;
  - the float solver: broke the boot stripe.
- **Fix:** the bands are now cut from the whole shell before the seam split. Islands match v7i (Lower_white 3,
  Lower_ink 3), the STL gate passes and every part is manifold.

**Evidence**
- **Section at x = 30** (`views/details/hull-wall-section.png`): bottom wall 0.89 → 1.26 mm.
- **G-code** (`scripts/wall_fill.py`): for each Hull_lower layer, the deposited volume per layer height is compared
  with the STL cross-section area.
  - The ratio is 0.90–0.97 for both v7i and v7j (median 0.97), so the walls are solid with no gaps.
  - At print z 2.9, inner wall plus solid infill rises from 140 to 384 mm² per layer.
  - The one low layer, print z 7.88, is a bridge-only sub-layer between 7.72 and 8.04, which score 0.96 and 0.97.
- **Mating with the printed v7i upper half** (seam slices at z 2.45 and 2.55, x −98 to 80):
  - the outer outline and lug stations are identical to 0.01 mm;
  - only the inside of the wall at x < −70 moves inward by up to 1.2 mm, where the stern is shallow and the thicker
    bottom reaches the seam;
  - Upper_ink and Upper_teak are unchanged.

  So the new lower half takes the old upper half flush, on a wider glue land aft.
- **Joint (answer to the user):** the 4 lug pins only locate the halves. Use 6.5 mm of 2 mm rod; 1.75 mm filament has
  about 0.2 mm of play per side. Slow epoxy on the 1.7 mm seam land holds and seals. Dry-fit and sand off elephant foot
  on both seam faces first.

**Challenge/defend**

| Reviewer | Verdict | Challenge | Defence / decision |
|---|---|---|---|
| GPT-6.2-sol | ACCEPT | Leave the cup and topsides alone; prefer 2 mm pins; prove the bottom prints solid, especially at bow and stern | **Done:** the G-code fill check above; 2 mm rod in the README |
| Opus 5.5 | ACCEPT | 1.0 mm would gain little; 1.75 mm filament is loose; dry-fit and sand elephant foot; quote 75 balls / 12.0 g; ask what "thin" meant | **Done:** README assembly step 2 and ballast. Cup and topside thickening offered, not done |
| Grok 4.7 | ACCEPT (1, 2); CHALLENGE (3) | 1.2 mm is the minimum that adds a line; a 6.5 mm rod in 7 mm of hole sits 0.5 mm shy, so it cannot hold the land open; 1.75 mm filament will not register the boot stripe | **Accepted:** the README now says to align the stripe by eye and tape or clamp while the epoxy cures if filament is used. 2 mm rod stays the first choice |

**As built (v7j)**
- **Parts:**
  - Lower_blue 11.57 cm³ (8.73), Lower_white 0.88, Lower_ink 0.86;
  - Hull_lower 15.9 g (12.2); printed 50.8 g, 50.2 g on board.
- **Plate:** 13 h 10 min model time (13 h 17 min total); 212.2 g filament (80.8 / 46.9 / 55.6 / 28.9 g); 235 layers,
  321 colour changes.
- **Float:**
  - 75 balls (12.0 g, was 98), all-up 64.0 g; trim 0.09° bow-down;
  - GM 16.0 mm (18.6); GZ 2.7 / 5.0 / 6.8 mm at 10 / 20 / 30°; AVS 132° (140°); the cockpit floods at 130°;
  - heel with the full sail at 2 m/s: 14° (12°).
- **Stand:** STL unchanged.
  - Tipping at 30 / 27 / 28° sideways and 32 / 29 / 29° forward;
  - G margins 8.6 / 7.4 / 8.5 mm;
  - neck SF 10.6 static, 3.5 under a 3 g knock.
- **Reprint:** only Hull_lower (Lower_blue, Lower_white, Lower_ink).
