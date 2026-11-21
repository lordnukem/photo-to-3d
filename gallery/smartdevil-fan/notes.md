# smartdevil-fan

## What the user asked for
"Render this USB table top fan for 3D printing. Time the process for benchmark." Five photos, no sizes.

## Parts (from the photos)
- **Head housing**: a thick ring like a short tyre, matte black. The outside bulges slightly, with a moulding
  seam around the middle. The front edge has a stepped bezel; the back edge is well rounded.
- **Front grille** (photo_05): about 32 spiral bars from a centre disc to the rim, set a little behind the front
  face. The centre disc carries "SMARTDEVIL" in light letters.
- **Rear grille** (photo_03): about 34 gently curved bars, domed out behind the housing (about 8 mm, photo_01 and
  photo_02), and a larger centre disc.
- **Rotor**: 5 blades (product listing), seen through the grilles.
- **Base**: a cylinder; a narrow groove at about 2/3 height; above it a taller upper section that the head sits
  down into. USB-C port low on the back (photo_03).
- **Dial**: a small round knob with a white index line, at the front of the base's upper section, right of
  centre (photo_05; side views photo_02 and photo_04).

## Sizes
| size | value | source |
|---|---|---|
| total height | 173 mm | listing of the SmartDevil stepless-knob desk fan (17.3 x 14.5 x 9.8 cm), the closest match found |
| housing diameter | 145 mm | listing width |
| housing depth (front face to back edge) | 79 mm | est, photo_02 at 0.164 mm/px |
| rear grille dome | 8 mm | est, photo_02 |
| front opening / grille radius | 62 mm | est, photo_05 |
| front hub disc diameter | 43 mm | est, photo_05 |
| rear hub disc diameter | 50 mm | est, photo_03 |
| base diameter / height | 66 / 36 mm | est, photo_02, photo_05 |
| dial diameter / reach | 13 / 9 mm | est, photo_04, photo_05 |
| head's lowest point | 31 mm above the table | est, photo_02 |

Check: 31 + 145 = 176 mm total height, against 173 in the listing. The depth comes to about 88 mm against the
listing's 98 (the listing may include the dial or packaging).

## Materials and colours
Matte black plastic for everything; "SMARTDEVIL" in light warm grey; the dial's index line is white.

## Photos (direction taken from)
photo_01: from above (top of the head). photo_02: right side (front on the left). photo_03: back, slightly
above. photo_04: left side. photo_05: front, slightly above.

## For 3D printing
Four printable parts, each exported as a single closed solid STL in millimetres:
1. base (with the dial and a saddle that the head sits in),
2. housing (ring + rear grille),
3. front grille (with the hub and raised logo; drops into the housing, 0.2 mm clearance),
4. rotor (5 blades, hub, axle that glues into the rear hub).
Minimum features: grille bars 2.0 mm, blades 1.6 mm, logo raised 0.4 mm (fine for resin, marginal on FDM).
A printed fan is a display model: no motor or electronics.

## Open questions and assumptions
- Scale from a retail listing, not measured.
- Head upright (the real head tilts up to 20 degrees).
- Bar counts and curves from the photos, approximate.

## Rounds
1. First build: base, housing, front grille and rotor; checks found the grille bars as specks (mixed units)
   and fixed it; all four print parts single closed solids. Renders from all five photo angles: shape right;
   base too narrow; rear bars too curved.
2. Base 72 mm, rear bars nearly radial (40), front bars 36 with 110 degree sweep. Matches the photos;
   remaining differences are fine detail. Fit check: rotor axle overlapped the rear hub by 2.2 mm, so it was
   shortened to stop 0.1 mm short.
