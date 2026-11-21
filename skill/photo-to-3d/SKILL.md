---
name: photo-to-3d
description: Build a 3D model of an object in Blender from one or more photos and/or a description (sizes, materials, instructions). Claude writes a parametric Blender script, renders it next to the photos, corrects it, and delivers GLB, OBJ and .blend files with renders. Use when someone wants a 3D model of something they photographed or describe.
---

# photo-to-3d: photos + notes → a Blender model

The user gives photos of an object (one or several angles), and may add notes: sizes, materials, what to
leave out, how detailed, what the model is for. You model the object as a Python script for Blender
built from the library in `scripts/p3d_blender.py`, render it from the photos' angles, compare, fix, and
deliver. The model is an interpretation of the photos, not a measurement: say so, and list every
assumption.

Good at: manufactured objects (bottles, cups, boxes, gadgets, furniture, tools, packaging, simple parts),
including glass, clear plastic and water. Poor at: organic forms (faces, animals, plants, clothing):
offer a simplified stand-in and say it is one.

## Commands

`M=~/.claude/skills/photo-to-3d/scripts/model3d` (model folders and the Python environment live in `$PHOTO3D_HOME`, default `~/photo-to-3d`; the paths below assume the default)

| command | what it does |
|---|---|
| `$M check` | Blender found, its Python can load numpy and Pillow, font present (run once per session) |
| `$M new NAME --photo F [--photo F2 ...] --notes "..."` | makes `~/photo-to-3d/models/NAME/` with `photos/`, `notes.md`, `build.py` (template) |
| `$M build DIR [--clay] [--views a,b]` | preview: 360x480, 32 samples, about 30 s per view; writes `out/comparison-preview.png` |
| `$M build DIR --final` | final: 600x800, 160 samples, about 10 min per view on a 2-core CPU; run in the background |
| `$M sheet DIR [--final]` | redraws only the comparison sheet from the last build |

A build always exports `out/NAME.glb`, `out/NAME.obj` (+ `.mtl` and images), `out/NAME.blend` and
`out/model_info.json` (sizes, parts, open-mesh problems, assumptions, render list). It prints `BUILD OK`; anything
else is a failure, and the log is `out/build-<quality>.log`.

## Workflow

1. **Collect.** Photos the user attaches are saved as files (in Claude Code under `~/.claude/uploads/...`); pass those paths to
   `model3d new --photo`. HEIC can't be read: ask for JPG or PNG. Put the user's own words in `--notes`.
2. **Look and write it down** in `notes.md` before writing any code:
   - the parts (body, lid, handle, strap, print, ...), and what each is made of and its colour;
   - a size table with the source of every size: *given* (the user said) or *est* (from the photo or from
     what such objects usually measure). Derive the other sizes from one known size by proportion in the
     photos. If nothing gives the scale, use the typical size of such an object and make that the first
     entry in `ASSUMPTIONS`;
   - for each photo, the direction it was taken from (azimuth right of the front, elevation), which becomes
     a view in `VIEWS`, so the sheet compares like with like.
3. **Write `build.py`** (start from the template or the nearest example in `examples/`): all sizes in `DIMS`,
   assumptions in `ASSUMPTIONS`, views in `VIEWS`, and `build(lib)` returning the list of parts. Conventions:
   metres, Z up, the object standing on z = 0 centred on the Z axis, the front facing -Y.
4. **Preview and compare**: `$M build DIR --clay`, then Read `out/comparison-preview.png`. Check in order:
   silhouette and proportions, every part present and in the right place, colours and materials, prints and
   labels. `--clay` renders every view a second time with everything in plain grey (glass becomes opaque,
   prints are hidden), which shows the outer shape clearly, at twice the render time. A `WARNING:` line
   (a part with open edges) needs fixing unless the part is meant to be open. Fix the biggest difference first.
   Stop after about three rounds or when only fine detail differs. Don't chase render noise.
5. **Final renders** (`--final`, in the background) once the preview is right. Tell the user how long it
   will take.
6. **Deliver**: send `out/comparison-final.png` and the GLB to the user (with SendUserFile where that tool exists, otherwise give the paths); list the files; state the size;
   list the assumptions and the visible differences from the photos; offer what would improve it (a
   measurement, a photo from another side, a closer look at a detail).

## Library (`lib` in build.py)

Geometry (each returns the Blender object; give every part a unique name):
- `lathe(name, profile, mat)`: spin [(r, z), ...] around Z. Start and end the profile on the axis for a
  closed solid; for a hollow part trace the outside up and the inside back down. `arc(cx, cz, r, a0, a1, n)`
  adds a rounded corner (degrees). A closed loop that never touches the axis gives a ring.
- `rounded_box(name, (sx, sy, sz), centre, bevel, mat)`
- `cylinder(name, radius, length, centre, mat, axis="Z"|"X"|"Y", radius_top=None)` (a cone with radius_top)
- `sphere(name, radius, centre, mat, scale=(1, 1, 1))` (an ellipsoid with scale)
- `extrude(name, [(x, y), ...], z0, z1, mat, bevel=0)`: a prism from an outline (counter-clockwise from above)
- `tube(name, [(x, y, z), ...], radius, mat, closed=False)`: smooth round tube (handles, cables, bent straws)
- `ribbon(name, points, width, thickness, mat, up=(0, 0, 1), closed=False)`: flat band (straps, belts)
- `transform(ob, rotate_deg=(x, y, z), about=point, move=(dx, dy, dz))`: turn and move a part's mesh
- `boolean(target, cutter, "DIFFERENCE"|"UNION"|"INTERSECT")`: holes, slots and openings; both must be closed

Printing (labels, logos, text):
- `text_image(text, lib.work_path("x.png"), color=(60, 60, 60))`: a transparent PNG of one line of text; pass
  `color` by keyword as sRGB 0–255 integers (not `lib.color()`, which is for materials)
- `crop_image(photo, (left, top, right, bottom) as shares 0..1, lib.work_path("x.png"))`: a label from a photo
- `decal_on_cylinder(name, mat, radius, z0, z1, centre_deg, width, along="height"|"around")`: on a round
  surface; "height" = reading down the side, "around" = a wrap label
- `decal_on_plane(name, mat, centre, (w, h), facing="-Y"|"+Y"|"-X"|"+X"|"+Z")`: on a flat face
- `image_material(name, png, color=None)`: material for a decal; pass `color=` by keyword (a linear colour,
  e.g. `lib.color("#333333")`) to replace the image's own colours
- `text_mesh(name, text, size, depth, centre, mat)`: text as real geometry (raised, or cut in with `boolean`):
  use this, not a decal, when the model is for 3D printing

## 3D printing

When the model is for printing, define `PRINT_PARTS = {"part": ["object", ...], ...}` in build.py: the separate
pieces someone will print and assemble. Each build then writes `out/print/<part>.stl` in millimetres, each
part merged into one solid, and prints `print part NAME: size, volume, open edges, shells`. Every part must
show **open edges 0 and shells 1**; anything else is a `WARNING` and a broken print (loose pieces, holes).
- Design for the printer: bars and walls at least 1.6–2 mm, raised text at least 0.4 mm, a clearance of
  0.2–0.3 mm where one part slides into another.
- **Printed parts must not overlap in the assembled model**: two parts can't occupy the same space. Check every
  joint (an axle, a peg, a part sitting in a saddle) and leave a gap of 0.1 mm or more, or cut a socket.
- Split parts so that each prints on a flat face, and say how to orient and assemble them (glue points).
- Give sizes, volumes and the minimum features in the delivery, and say it is a display model when the
  original has electronics or moving parts.
- `examples/desk_fan.py` is a full printable model: four parts, grilles, blades, raised logo, saddle fit.

Materials:
- `color("#8c9eb3")` / `color((140, 158, 179))`: sRGB → linear. **Always convert colours read off a photo**:
  Blender's material colours are linear, and raw photo values make everything look paler.
- `photo_color(photo, box)`: the average colour of an evenly lit patch of a photo, already converted
- `preset(kind, name, color=None, **overrides)`, with kinds `plastic, glossy_plastic, rubber, metal,
  brushed_metal, ceramic, wood, fabric, clear_plastic, glass, water, frosted`
- `material(name, color, roughness, metallic, transmission, ior, alpha, coat)`: anything else
- `see_through(name)`: thin clear parts lying on opaque ones (see Pitfalls)

## Pitfalls (each one found in testing)

- **A refracting clear part lying on an opaque one renders black.** The renders run without caustics (they
  cause most of the grain), so no light passes through glass onto a diffuse surface. Use `see_through` for thin
  clear windows and inserts; keep `clear_plastic`/`glass` for real volumes such as a bottle body.
- **Overlapping clear and opaque solids** also render black or wrong: leave a hairline gap (0.05 mm).
- **Water inside a container**: make it a separate solid 0.2 mm inside the inner wall, not touching it.
- **Decals** sit 0.08–0.15 mm above the surface; the library handles the strip count on round surfaces.
- **The comparison is approximate**: the studio lighting differs from the photo, so compare shapes and
  layout, and judge colours with care.
- **Renders are grainy at preview quality**: Blender builds without OpenImageDenoise (such as Ubuntu's package) have no denoiser. Final quality is cleaner.
- **To stop a running build**, kill Blender by its process ID (`pgrep -x blender`). Never use `pkill -f` with
  a pattern, because it also matches and kills your own shell command.
- **OBJ cannot describe glass or transparency**: the GLB keeps transmission and IOR; recommend the GLB.
- **Units**: if you build a part in millimetres and scale it at the end, give every coordinate of that part in
  millimetres. Mixing in values already in metres shrinks them to specks (it happened with grille bars; the
  shell count of the print part caught it).

## Files

- `scripts/p3d_blender.py`: the library (runs inside Blender)
- `scripts/blender_runner.py`: builds, checks, exports and renders one model (called by model3d)
- `scripts/model3d` / `model3d.py`: the command above (runs in `~/photo-to-3d/.venv`, which also gives
  Blender its numpy and Pillow)
- `templates/`: `build_template.py`, `notes_template.md`
- `examples/`: `desk_fan.py` (printable: PRINT_PARTS, grille bars as ribbons, pitched blades, text_mesh logo,
  saddle cut with boolean), `water_bottle.py` (lathe body, water, lid, flip cover, strap ribbon, straw, printed text),
  `mug.py` (hollow lathe, tube handle, wrap-around text), `tissue_box.py` (boolean opening, label cut out of a
  photo, sRGB colour)
- Model folders: `~/photo-to-3d/models/NAME/{photos/, notes.md, build.py, out/}`
