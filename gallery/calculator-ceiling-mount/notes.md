# calculator-ceiling-mount

## What the user asked for
"I need to mount this on the ceiling with the button facing down. Model the mount for me." Five photos of a
Canon LS-88Hi III calculator; no sizes.

## The calculator (from the photos and Canon's spec)
| size | value | source |
|---|---|---|
| length x width x height | 143 x 89.5 x 25 mm, 90 g | Canon spec (height = table to the top of the raised display end) |
| thickness at the keypad end | 9.0 mm | est photo_01 (8.7 mm at 9.2 px/mm) |
| underside flat from the keypad end | 85 mm | est photo_02, photo_04 |
| display section tilt | 16 deg | est photo_02 plus the spec height |
| key rows (centres from the keypad end) | 21, 34, 47, 60, 72 mm | est photo_05 |

Shape: a plate about 9 mm thick; the keypad section lies flat, the display section is bent up 16 degrees, so its
underside is off the table. Pale blue body, white, blue and red keys, solar cell at the display end.

## Photos (direction taken from)
photo_01: keypad end, low. photo_02: left side. photo_03: display end. photo_04: right side. photo_05: from above.

## Design
Modelled the way it prints (plate on the bed, calculator in it keys up); on the ceiling it is turned over.
- Plate 3 mm with two countersunk holes for 4 mm screws under the keypad section, a window under the display
  section (nothing rests there).
- Side rails 2.4 mm, 5 mm above the calculator's underside, 0.4 mm clearance; they rise with the display section
  and brace the end wall.
- End wall square to the display end face (0.6 mm gap) with a 3 mm lip over the face, 0.6 mm above its top corner.
- Turn button at the keypad end on a boss (M3 self-tapping pivot screw): its tongue covers 5 mm of the keypad
  end's face (0.4 mm gap), and a tooth (outer face an arc round the pivot) fills the 4 mm loading gap so the
  calculator cannot slide back out from under the lip.
- Fitting: hold the calculator keys down, push the display end up and under the lip, swing the keypad end up
  to the plate, turn the button over it.

## Fit checks (build.py prints them)
- installed: no clash with the mount or the button;
- turning the button 0-90 deg: no clash;
- path in, display end 1.5 mm short of home and tilted 0-20 deg about the lip: no clash.

## Rounds
1. First build: shape matches the photos; all fit checks clear. Mount STL had 3 open edges: the window cutter's
   rounded bottom edge just reached the plate's underside. Taller cutter -> mount and turn button both one closed
   solid (trimesh agrees).
