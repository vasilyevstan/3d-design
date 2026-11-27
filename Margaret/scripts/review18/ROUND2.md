# Rev 18 round 2 — as-built J-tang with front lip (v7o)

Round 1: GPT and Opus "adopt with changes" (open-front slot, front swing-in); Grok "adopt with changes" but add a
front lip because an open front only holds fore-aft by a ~0.2 gf gravity moment (a finger nudge of ~1.5 mm or a 16 deg
bow-down tilt walks the tang out). Decision: Grok's lip adopted (the user's complaint is "wobbly"); GPT/Opus items kept
where compatible.

## As built (prescale mm; exported x is x1.0346, y/z unscaled). Mast prints on its aft face (print z = model x),
furler prints flat on its y=-0.6 face; plate 3 = 0.16 mm layers, 0.2 first layer, Arachne, 2 walls, supports
build-plate only.
- Cap x 24.1..26.75 (2.65), z 235.0..240.6, y -1.85..1.65 (3.5 wide, centred on the slot), top round 0.25.
- Slot y -0.85..0.65 (1.5 wide), cheeks 1.0 / 1.0; aft wall 0.8 (x 24.1..24.9); floor z 237.8.
- Front lip x 26.15..26.75 (0.6 thick), floor..z 239.4 (1.6 high, top 1.2 below the cap top), 0.4x45 chamfer on its
  aft-top edge; above z 239.4 the slot is open forward. 0.3 mm lead-in on the cheek tops.
- J-tang (y -0.6..0.4 = 1.0 thick = 0.2+5x0.16 layers): leg x 25.1..25.95 (0.85), bottom z 238.0, 0.25 chamfer on
  its aft-bottom corner only (square front locks on the lip); bridge underside z 239.6 with a 0.3 root fillet parallel to
  the lip chamfer (0.35 clear); bridge to the body front part (aft face x 27.35 = cap front + 0.6), tang top z 241.0.
- Furler body kept >= 0.6 mm in front of the cap (mainsail head lashing through the masthead hole at z 236.4).
- Furler axis, foot tab (4.2, 3.2 in the pocket) and the stemhead pocket unchanged; hull STLs geometrically unchanged.

## Evidence (review18/tang_fit.py -> yacht-build/v7o/tang_fit.json; 0.02 mm raster at mid-tang y)
- Parked: overlap 0; gaps down 0.18, aft 0.20, forward (lip) 0.22; y: mast -1.85/-0.85/0.65/1.65, tang -0.6/0.4.
- Drop-in straight down from 2.0 mm lift: clear at every 0.1 mm.
- Lift needed before any forward motion (0..2.5 mm at the head) is free: 1.1 mm (vertical lock faces ~1.0 mm).
- Let go 1.8 mm up and 0.3 mm forward, gravity only (slide down the stay / swing aft): comes to rest seated
  (0.24 down the stay, head 0.15 fwd: leg on the floor against the lip) — inside the pocket, captive.
- Settle from design: 0.18 down the stay, 0.04 aft. Head body to cap front 0.62 design / 0.64 settled.
- Tab 3.2 in the pocket, floor gap 0.8 design / 0.62 settled; mast standing 0.5..3.0 mm high: overlap 0 at all,
  tab left 2.68/2.16/1.64/1.11/0.59/0.07.
- Fitting: mast fully seated; tab into the stemhead pocket; hold the head ~1.6 mm up over the slot; lower it.
  Removal: lift the head ~1.6 mm, then forward. During fitting the tab keeps ~1.6 mm in its pocket.

## Questions
1. Is the lip worth it vs the open front (defend or attack with numbers)? Anything that will jam, crack or not print
   (lip = 1.5 mm bridge, 4 layers; leg 0.85 x 1.0 mm; aft wall 0.8 = 4-5 layers)?
2. Any change that is clearly necessary before the user reprints plate 3? Keep it short; no new mechanisms.
