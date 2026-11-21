# SMARTDEVIL desk fan: printing guide

Display model (no motor or electronics), 176 mm tall, 145 mm wide. All files are in millimetres, and each
part is one watertight solid (checked: 0 open edges, 1 body).

| file | size (mm) | volume | print on | supports |
|---|---|---|---|---|
| `housing.stl` | 145 × 89 × 145 | 334 cm³ | its flat front face (the bezel ring) | yes, for the rear grille dome (tree supports) |
| `front_grille.stl` | 124 × 5 × 124 | 33 cm³ | its flat back, logo facing up | none |
| `base.stl` | 72 × 79 × 36 | 132 cm³ | its flat bottom | under the dial only |
| `rotor.stl` | 107 × 83 × 107 | 23 cm³ | the back end of the axle | yes, under the pitched blades (or print in resin) |

- Bed: the housing needs at least 150 × 150 mm.
- Minimum features: grille bars 2.0 mm wide, blades 1.6 mm thick, the logo raised 0.4 mm. The logo letters are
  fine for resin and a 0.25 mm nozzle; with a 0.4 mm nozzle they will be soft.
- Volumes are of solid parts: with 15–20 % infill a slicer will use far less material.

## Assembly (glue, e.g. cyanoacrylate)
1. Glue the rotor's axle end onto the centre of the rear hub, inside the housing (the axle stops 0.1 mm short
   of the hub, so it seats flat).
2. Drop the front grille into the front of the housing (0.2 mm clearance) and glue it at the rim.
3. Set the head into the saddle on top of the base (0.3 mm clearance) and glue it.
