# Margaret — Revision 17 round-2 challenge/defend brief (v7n, built, sliced, gated)

Context: read `review17/BRIEF.md` (round 1) first; round-1 verdicts: GPT NO-GO as written (fixes ranked: mast seating,
boom lashing, cleats + colour verification, leak test), Grok GO, Opus GO-with-corrections (`review17/GPT_R1.md` holds
the GPT text). All folders are relative to
`/Users/stanvasilyev/.copilot/session-state/8c5066cc-857a-4e5b-8c5e-ea6ba2a01c4f/files`.

## What was built (v7n) — adopted from round 1
1. Mast seating: bore clearance 0.15 -> 0.25 mm/side; 0.45 mm seam-mouth relief on both halves; support blockers over
   both mast bores in the 3MF. Gauge for "mast fully home": collar top z 23.2 -> gooseneck-saddle top z 43.0 =
   **19.8 mm** visible between them. Heel z -3.0 over socket floor -3.3. Seated: shroud-frame feet rest on the
   chainplate block tops (0-0.3 mm), tabs 0.2 mm above the pocket floors.
2. Cleats: 6 navy horn cleats (4.2 x 1.2 x 2.72 mm on a 3.0 x 1.6 flange), each 0.42-0.44 mm inside the toe rail, long
   axis tangent to the local toe-rail line: bow (75, +-15.34, -+26 deg), spring at max beam (-6, +-29.54, 0),
   quarter (-80, +-26.06, +-8 deg) (prescale x; exported x = 1.0346 * (x - 3.2)). Teak recess under each cleat is now
   the flange outline + 0.1 mm, yawed with the cleat (round-1 Opus: axis-aligned box left white wedges).
3. Boom: object now named "Boom" in the 3MF (plate 3). Connection = thread lashing through the boom's forward hole,
   wrapped TIGHT round the mast on top of the gooseneck saddle (the saddle only stops the wrap sliding down; the boom
   does not "sit on" it); mainsheet from boom hole 4 from aft (x -17) to the printed coachroof eye. No printed fork.
4. One multi-plate 3MF `yacht-build/v7n/plate/Margaret-P2S.3mf`, objects named, object-level filament set:
   P1 Hull_upper (white/navy/teak) 7h01m; P2 Hull_lower + Fin_cap + Ballast_cup + Rudder (blue/white/navy) 2h41m;
   P3 Mast(+shroud frame) + Furler + Boom + 2 wheels (white/navy) 44m; P4 Stand (navy) + Display_sail (white/navy)
   1h05m. Plates 1-3 = 10h25m, 51.65 g PLA on board (Hull_upper 25.79, Hull_lower 15.88, Fin_cap 2.95,
   Ballast_cup 2.22, Rudder 0.31, Mast 2.37, Furler 1.53, Boom 0.42, wheels 0.09 each). Stand 10.61, Display_sail 4.54.

## New evidence (all from the sliced G-code / exported STLs)
- White keel fixed: per-object G-code tool attribution Fin_cap 100 % T2 (blue), Ballast_cup 100 % blue, Stand 100 % navy;
  Hull_lower 13.93 g blue / 0.9 white / 1.05 navy. (A parser bug that missed the indented start-G-code `T1` was fixed.)
- Mast bore as printed (every layer, both halves): 4.25 x 3.11 mm (x incl. 1.0346 scale) vs heel 3.72 x 2.59 ->
  0.26 mm/side. Support inside the bores: only one loose 22-23 mm first-layer loop at z 0.2 on each plate, no column;
  the lower socket roof prints as a bridge + solid infill.
- Joint fits (rudder bore halves r 1.23, bulb posts/holes, fin socket 3.40 x 18.83 vs tenon 3.19 x 18.62, rudder stock)
  identical to v7m to 0.003 mm.
- Name gates on plate 1: transom 17/17 navy layers, bow 19/19, every transom letter stroke present -> PASS.
- Compatibility with the owner's already printed (v7m) lower hull: vertical ray-cast every 0.1 mm of all lower parts and
  the upper's mating zone (z < 6.5) -> identical outside the mast zone (x 19-28, |y| < 4); Lower_ink 22 of 128,630
  columns differ by <= 0.07 mm (re-meshing on the inner wall). A v7n upper therefore mates a printed v7m lower unless
  the halves are already glued; in the mast zone the old lower socket keeps 0.15 mm/side (sand the heel if it binds).
- Rudder tube probe: sealed, opens only to the cockpit sole; one pre-existing local thin spot 0.45-0.5 mm over < 0.1 mm
  height at z ~ -1.1 (also in v7m). Rudder mouth wets only at ~155-159 deg heel.
- Stability (sliced masses, PLA sailing 50.12 g excl. display furler + 1.78 g extras): displacement 63.88 g, lead
  11.97 g = 75 x 3 mm balls (cavity 127 discrete / ~20 g), G (-4.0, -3.47), CLR (-6.1, -19.6), GM 16.0 mm,
  AVS 132 deg, reserve buoyancy 165 g, trim 0.08 deg bow down with lead centroid x -9.1. Full paper main 66.4 cm2,
  CE x -2.0 (4 mm = 2.3 % LWL ahead of CLR): heel 3.6/7.9/13.9/28.7 deg at 1/1.5/2/3 m/s; medium 32.3 cm2: 5.5 deg
  at 2 m/s, 12.2 at 3; start 25.5 cm2: 9.7 at 3 m/s. Deck edge immerses at 31 deg.
- Island checks: Upper_ink 96 components (quarter cleats now join the toe-rail/caulk network, all navy), Upper_teak 62,
  no tiny islands; all exported parts non-empty and manifold (build gates).

## Images (view tool, absolute path prefix above + `review17/img/`)
view-1..6.png (stage renders: profiles, quarters, deck plan, exploded bulb), Margaret-views.png (sheet),
Margaret-sail-rigging.png, Margaret-afloat.png, deck_cleats.png, cleat_bow17.png, cleat_spring.png, cleat_quarter.png,
gooseneck.png (lashing round the mast on the saddle, through the boom's forward hole), namecheck.png.

## Planned README changes (challenge them)
Plates table; cleat positions; boom connection (as above, holes labelled from aft); mast seating + 19.8 mm gauge;
fix for already printed parts (2 mm bit only, stop 5.8 mm below the seam face, pick the loose loop/D-corners, sand the
heel if it binds; reprint the upper for the cleats; v7m lower compatible unless glued); wind table (full main <= ~2 m/s,
medium <= ~3 m/s, start sail above); deliberate proportion deviations (draft 55.5 vs 30.3 scale, luff 188 vs 231,
rig ~81 %); rudder-tube seam ring glued + submerged bubble test before ballasting.

## What to return (<= 450 words)
Per item 1-4 and the evidence: ACCEPT / CHALLENGE with concrete reasons and numbers (inspect the images). Point out
anything that would make the print fail, mis-assemble, look clearly wrong vs an SO43, or be unseaworthy. No new
tooling, no hull-shape changes, no restyling. End with a final GO / NO-GO for delivery of v7n.
