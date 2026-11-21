"""Building blocks for modelling objects in Blender from photos (imported by a model's build.py).

Conventions: metres, Z up, the object stands on z = 0 centred on the Z axis, its front faces -Y (the
camera of the "front" view looks along +Y). Every function that makes a part returns the Blender object;
build(lib) in the model's build.py returns the list of parts to export.

Geometry   arc, lathe, rounded_box, cylinder, sphere, extrude, tube, ribbon, boolean, transform
Printing   text_image, text_mesh, crop_image, decal_on_cylinder, decal_on_plane
3D print   export_print_parts (STL per printable part, in mm, merged and checked)
Materials  color, photo_color (sRGB -> linear), material, preset (PRESETS), see_through, image_material
Files      work_path (where to write generated images)
"""
import math
import os
import sys

try:                         # Ubuntu's Blender has neither numpy (glTF export needs it) nor Pillow
    import numpy  # noqa: F401
    import PIL  # noqa: F401
except ImportError:
    sys.path.append(os.path.expanduser(
        f"{os.environ.get('PHOTO3D_HOME', '~/photo-to-3d')}/.venv/lib/"
        f"python{sys.version_info.major}.{sys.version_info.minor}/site-packages"))

import bmesh
import bpy
from mathutils import Matrix, Vector

# DejaVu Sans: $PHOTO3D_FONT, else the usual places on Debian/Ubuntu, Fedora, Arch and macOS
FONT_PLACES = [os.environ.get("PHOTO3D_FONT", ""), "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
               "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf", "/usr/share/fonts/TTF/DejaVuSans.ttf",
               "/usr/share/fonts/dejavu/DejaVuSans.ttf", "/Library/Fonts/DejaVuSans.ttf",
               os.path.expanduser("~/Library/Fonts/DejaVuSans.ttf")]
FONT = next((f for f in FONT_PLACES if f and os.path.exists(f)), FONT_PLACES[1])
WORK_DIR = "."                   # set by blender_runner.py to OUT/work


def work_path(filename):
    """Where to write a generated file (a text image, a crop of a photo) for this build."""
    os.makedirs(WORK_DIR, exist_ok=True)
    return os.path.join(WORK_DIR, filename)


# ------------------------------------------------------------------ objects

def _link(name, me, material, smooth_angle):
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if material is not None:
        me.materials.append(material)
    if smooth_angle is not None:
        for o in bpy.context.selected_objects:
            o.select_set(False)
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(smooth_angle))
        ob.select_set(False)
    return ob


def _from_bmesh(name, bm, material, smooth_angle=40.0):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return _link(name, me, material, smooth_angle)


def arc(cx, cz, r, a0, a1, n=8):
    """Points (r, z) of an arc in a lathe profile; angles in degrees; the start point is left out, the end kept."""
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             cz + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(1, n + 1)]


def lathe(name, profile, material, steps=128, smooth_angle=40.0):
    """Spin a profile [(r, z), ...] around the Z axis.

    A profile that starts and ends on the axis (r = 0) gives a closed solid: trace the outside from the
    bottom centre up, then the inside back down (for a hollow part) and end on the axis. A closed loop of
    points that never touches the axis (first point repeated at the end) gives a ring.
    """
    bm = bmesh.new()
    verts = [bm.verts.new((r, 0.0, z)) for r, z in profile]
    edges = [bm.edges.new((a, b)) for a, b in zip(verts[:-1], verts[1:])]
    bmesh.ops.spin(bm, geom=verts + edges, cent=(0, 0, 0), axis=(0, 0, 1), dvec=(0, 0, 0),
                   angle=2 * math.pi, steps=steps, use_merge=True, use_duplicate=False)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _from_bmesh(name, bm, material, smooth_angle)


def rounded_box(name, size, centre, bevel, material, segments=4):
    """Box of size (x, y, z) around centre with rounded edges; bevel at most a little under half the smallest side."""
    bevel = min(bevel, 0.45 * min(size))
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(centre), verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges), offset=bevel, segments=segments, profile=0.5,
                        affect="EDGES", clamp_overlap=True)
    return _from_bmesh(name, bm, material)


def cylinder(name, radius, length, centre, material, axis="Z", segments=48, radius_top=None):
    """Solid cylinder (or cone with radius_top) of `length` along X, Y or Z, centred on `centre`."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=radius,
                          radius2=radius if radius_top is None else radius_top, depth=length)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)        # a pointed cone has one tip, not one per segment
    turn = {"Z": None, "X": Matrix.Rotation(math.pi / 2, 3, "Y"), "Y": Matrix.Rotation(-math.pi / 2, 3, "X")}[axis]
    if turn is not None:
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=turn, verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(centre), verts=bm.verts)
    return _from_bmesh(name, bm, material, smooth_angle=50.0)


def sphere(name, radius, centre, material, scale=(1.0, 1.0, 1.0)):
    """Sphere, or an ellipsoid with `scale`."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=radius)
    bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(centre), verts=bm.verts)
    return _from_bmesh(name, bm, material, smooth_angle=80.0)


def extrude(name, outline, z0, z1, material, bevel=0.0, segments=3):
    """Prism from a flat outline [(x, y), ...] (counter-clockwise seen from above), from height z0 to z1.

    For a part that stands in another plane, build it lying flat and turn it with transform().
    """
    bm = bmesh.new()
    bottom = [bm.verts.new((x, y, z0)) for x, y in outline]
    top = [bm.verts.new((x, y, z1)) for x, y in outline]
    bm.faces.new(list(reversed(bottom)))
    bm.faces.new(top)
    n = len(outline)
    for i in range(n):
        bm.faces.new((bottom[i], bottom[(i + 1) % n], top[(i + 1) % n], top[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=segments, profile=0.5, affect="EDGES",
                        clamp_overlap=True)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    return _from_bmesh(name, bm, material, smooth_angle=35.0)


def tube(name, points, radius, material, closed=False, resolution=12, segments=16):
    """Round tube (a handle, a cable, a straw that bends) through `points` [(x, y, z), ...], smoothly curved."""
    cu = bpy.data.curves.new(name + "_curve", "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = resolution
    cu.bevel_depth = radius
    cu.bevel_resolution = max(2, segments // 4)
    cu.use_fill_caps = not closed
    spline = cu.splines.new("NURBS")
    spline.points.add(len(points) - 1)
    for p, co in zip(spline.points, points):
        p.co = (*co, 1.0)
    spline.use_cyclic_u = closed
    spline.use_endpoint_u = not closed
    spline.order_u = min(4, len(points))
    tmp = bpy.data.objects.new(name + "_tmp", cu)
    bpy.context.scene.collection.objects.link(tmp)
    deps = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(deps))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=radius * 1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _from_bmesh(name, bm, material, smooth_angle=60.0)


def ribbon(name, points, width, thickness, material, up=(0.0, 0.0, 1.0), closed=False):
    """Flat band (a strap, a belt, a flat handle) along `points`: `width` measured along `up`, `thickness` sideways.

    Give the points densely enough to look smooth (e.g. 48 or more around a loop).
    """
    up = Vector(up).normalized()
    pts = [Vector(p) for p in points]
    n = len(pts)
    bm = bmesh.new()
    rings = []
    for i, p in enumerate(pts):
        prev = pts[(i - 1) % n] if closed or i > 0 else p
        nxt = pts[(i + 1) % n] if closed or i < n - 1 else p
        tangent = (nxt - prev).normalized()
        side = tangent.cross(up).normalized()
        rings.append([bm.verts.new(p + up * (sy * width / 2) + side * (sx * thickness / 2))
                      for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    for i in range(n if closed else n - 1):
        a, b = rings[i], rings[(i + 1) % n]
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    if not closed:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _from_bmesh(name, bm, material, smooth_angle=50.0)


def transform(ob, rotate_deg=(0.0, 0.0, 0.0), about=(0.0, 0.0, 0.0), move=(0.0, 0.0, 0.0)):
    """Turn a part about the point `about` (X, then Y, then Z, degrees) and move it; changes the mesh itself."""
    m = (Matrix.Translation(Vector(move) + Vector(about))
         @ Matrix.Rotation(math.radians(rotate_deg[2]), 4, "Z")
         @ Matrix.Rotation(math.radians(rotate_deg[1]), 4, "Y")
         @ Matrix.Rotation(math.radians(rotate_deg[0]), 4, "X")
         @ Matrix.Translation(-Vector(about)))
    ob.data.transform(m)
    ob.data.update()
    return ob


def boolean(target, cutter, operation="DIFFERENCE"):
    """Cut `cutter` out of `target` (or UNION / INTERSECT), apply it and delete the cutter. Both must be closed."""
    mod = target.modifiers.new("boolean", "BOOLEAN")
    mod.operation = operation
    mod.object = cutter
    mod.solver = "EXACT"
    for o in bpy.context.selected_objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = target
    target.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    # the cut leaves long thin faces that would smear the shading of rounded edges across flat areas;
    # weighted normals let the large flat faces keep their own
    wn = target.modifiers.new("weighted_normals", "WEIGHTED_NORMAL")
    wn.keep_sharp = True
    wn.mode = "FACE_AREA"
    bpy.ops.object.modifier_apply(modifier=wn.name)
    target.select_set(False)
    bpy.data.objects.remove(cutter)
    return target


# ------------------------------------------------------------------ printing: labels, logos, text

def text_image(text, path, letter_gap=0.14, width=2048, height=470, color=(235, 235, 235), font=FONT):
    """Transparent PNG with `text` in one line (left to right, letter tops up); returns the path."""
    from PIL import Image, ImageDraw, ImageFont
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    size = int(height * 0.86)
    while True:
        fnt = ImageFont.truetype(font, size)
        widths = [draw.textlength(ch, font=fnt) for ch in text]
        gap = letter_gap * size
        total = sum(widths) + gap * (len(text) - 1)
        if total <= width * 0.98 or size < 8:
            break
        size = int(size * width * 0.98 / total)
    top, bottom = draw.textbbox((0, 0), text, font=fnt)[1::2]
    x, y = (width - total) / 2, (height - (bottom - top)) / 2 - top
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=255)
        x += w + gap
    img = Image.new("RGBA", (width, height), (*color, 0))
    img.putalpha(mask)
    img.save(path)
    return path


def text_mesh(name, text, size, depth, centre, material, font=FONT):
    """Raised or engraved text as real geometry (for 3D printing, where a printed image does not exist).

    The text lies in the XY plane, reads along +X with its letters' tops towards +Y, faces +Z, and is `depth`
    thick, centred on `centre`. `size` is the font size (capital letters are about 0.73 of it). Turn it with
    transform(); cut it with boolean() to engrave.
    """
    cu = bpy.data.curves.new(name + "_text", "FONT")
    cu.body = text
    cu.font = bpy.data.fonts.load(font, check_existing=True)
    cu.size = size
    cu.extrude = depth / 2
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    tmp = bpy.data.objects.new(name + "_tmp", cu)
    bpy.context.scene.collection.objects.link(tmp)
    deps = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(deps))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=size * 1e-5)
    bmesh.ops.translate(bm, vec=Vector(centre), verts=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _from_bmesh(name, bm, material, smooth_angle=None)


def crop_image(photo, box, path, max_side=2048):
    """Cut a label or logo out of a photo: box = (left, top, right, bottom) as shares 0..1 of the photo."""
    from PIL import Image, ImageOps
    with Image.open(photo) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        w, h = im.size
        part = im.crop((round(box[0] * w), round(box[1] * h), round(box[2] * w), round(box[3] * h)))
        part.thumbnail((max_side, max_side))
        part.save(path)
    return path


def decal_on_cylinder(name, material, radius, z0, z1, centre_deg, width, along="height", flip=False, rows=80, cols=16):
    """Print an image on a cylinder (a patch 0.15 mm outside `radius`).

    The patch spans z0..z1 and `width` metres around the surface, centred `centre_deg` degrees right of the front.
    along="height": the image's left-to-right runs top to bottom (text that reads down the side, letter
    tops to the right); along="around": left-to-right runs around the surface, image up = +Z (a wrap label).
    flip turns the image 180 degrees.
    """
    r = radius + 0.00015
    span = width / r
    # enough columns that the flat strips sag far less than the 0.15 mm gap, or parts of the print sink into the surface
    cols = max(cols, math.ceil(span / (2 * math.acos(1 - 0.00003 / r))))
    a0 = math.radians(centre_deg) - span / 2
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    grid = [[bm.verts.new((r * math.sin(a0 + span * i / cols), -r * math.cos(a0 + span * i / cols),
                           z0 + (z1 - z0) * j / rows)) for j in range(rows + 1)] for i in range(cols + 1)]
    for i in range(cols):
        for j in range(rows):
            f = bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))   # normal outward
            for loop, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                u, v = ((1.0 - jj / rows, ii / cols) if along == "height" else (ii / cols, jj / rows))
                loop[uv].uv = (1.0 - u, 1.0 - v) if flip else (u, v)
    ob = _from_bmesh(name, bm, material, smooth_angle=80.0)
    ob["open_ok"] = True
    return ob


def decal_on_plane(name, material, centre, size, facing="-Y", flip=False):
    """Print an image on a flat face: a rectangle of size (width, height) 0.08 mm in front of `centre`.

    facing is the direction the face looks: -Y (front), +Y, -X, +X, +Z (top). The image is upright as seen
    from that side (for +Z: image up = +Y).
    """
    w, h = size
    axes = {"-Y": ((1, 0, 0), (0, 0, 1), (0, -1, 0)), "+Y": ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
            "-X": ((0, -1, 0), (0, 0, 1), (-1, 0, 0)), "+X": ((0, 1, 0), (0, 0, 1), (1, 0, 0)),
            "+Z": ((1, 0, 0), (0, 1, 0), (0, 0, 1))}[facing]
    right, up, out = (Vector(a) for a in axes)
    c = Vector(centre) + out * 0.00008
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    vs = [bm.verts.new(c + right * (sx * w / 2) + up * (sy * h / 2)) for sx, sy in corners]
    f = bm.faces.new(vs)
    for loop, (sx, sy) in zip(f.loops, corners):
        u, v = (sx + 1) / 2, (sy + 1) / 2
        loop[uv].uv = (1 - u, 1 - v) if flip else (u, v)
    ob = _from_bmesh(name, bm, material, smooth_angle=None)
    ob["open_ok"] = True
    return ob


# ------------------------------------------------------------------ materials

def color(value):
    """sRGB colour as seen in a photo or picker ("#8c9eb3" or (140, 158, 179)) -> the linear values Blender needs.

    Material colours are linear: typing photo values straight in makes everything look paler than the photo.
    """
    if isinstance(value, str):
        h = value.lstrip("#")
        value = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    out = []
    for c in value:
        c = c / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


def photo_color(photo, box):
    """Average colour of a region of a photo (box = left, top, right, bottom as shares 0..1), linear for Blender.

    Pick a patch in even light, away from highlights and shadows. The photo's lighting is part of the value,
    so treat it as a starting point and compare the renders with the photo.
    """
    from PIL import Image, ImageOps, ImageStat
    with Image.open(photo) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        w, h = im.size
        part = im.crop((round(box[0] * w), round(box[1] * h), round(box[2] * w), round(box[3] * h)))
        return color(tuple(ImageStat.Stat(part).mean))


def material(name, color=(0.8, 0.8, 0.8), roughness=0.5, metallic=0.0, transmission=0.0, ior=1.5, alpha=1.0,
             coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["Metallic"].default_value = metallic
    b.inputs["IOR"].default_value = ior
    b.inputs["Transmission Weight"].default_value = transmission
    b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat
    if alpha < 1.0:
        m.surface_render_method = "BLENDED"
    return m


PRESETS = {     # kind: keyword arguments for material(); color can be overridden
    "plastic": dict(roughness=0.45),
    "glossy_plastic": dict(roughness=0.15, coat=0.3),
    "rubber": dict(roughness=0.85),
    "metal": dict(metallic=1.0, roughness=0.25),
    "brushed_metal": dict(metallic=1.0, roughness=0.45),
    "ceramic": dict(roughness=0.2, coat=0.6),
    "wood": dict(roughness=0.6),
    "fabric": dict(roughness=0.95),
    "clear_plastic": dict(color=(0.97, 0.98, 1.0), roughness=0.03, transmission=1.0, ior=1.50),
    "glass": dict(color=(0.97, 0.99, 1.0), roughness=0.0, transmission=1.0, ior=1.52),
    "water": dict(color=(0.96, 0.985, 1.0), roughness=0.0, transmission=1.0, ior=1.333),
    "frosted": dict(color=(0.95, 0.95, 0.95), roughness=0.3, transmission=1.0, ior=1.45),
}


def preset(kind, name=None, color=None, **overrides):
    kw = dict(PRESETS[kind])
    if color is not None:
        kw["color"] = color
    kw.update(overrides)
    return material(name or kind, **kw)


def see_through(name, color=(0.92, 0.94, 0.96), roughness=0.08, alpha=0.35):
    """Thin clear plastic (a window, a lid insert) as a glossy, partly transparent surface.

    Use it instead of a refracting material for thin clear parts lying on an opaque part: the renders run
    without caustics, so a refracting slab blocks the light to the surface under it and shows up black.
    """
    return material(name, color, roughness, alpha=alpha)


def image_material(name, image_path, roughness=0.5, color=None):
    """Material that prints an image (with its alpha) - for decals. color replaces the image's colours."""
    m = material(name, color or (1.0, 1.0, 1.0), roughness)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.abspath(image_path))
    tex.extension = "CLIP"
    b = nodes["Principled BSDF"]
    if color is None:
        links.new(tex.outputs["Color"], b.inputs["Base Color"])
    links.new(tex.outputs["Alpha"], b.inputs["Alpha"])
    m.surface_render_method = "BLENDED"
    return m


# ------------------------------------------------------------------ checks, scene, renders, export

def measure(parts):
    """Bounding box, size and per-part mesh facts (open edges) of the evaluated parts."""
    deps = bpy.context.evaluated_depsgraph_get()
    lo, hi = [math.inf] * 3, [-math.inf] * 3
    info, problems = {}, []
    for ob in parts:
        ev = ob.evaluated_get(deps)
        me = ev.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.transform(ev.matrix_world)
        open_edges = sum(1 for e in bm.edges if not e.is_manifold)
        for v in bm.verts:
            for i in range(3):
                lo[i], hi[i] = min(lo[i], v.co[i]), max(hi[i], v.co[i])
        info[ob.name] = {"faces": len(bm.faces), "open_edges": open_edges,
                         "material": ob.data.materials[0].name if ob.data.materials else None}
        if open_edges and not ob.get("open_ok"):
            problems.append(f"{ob.name} has {open_edges} open edges (not a closed solid)")
        if len(bm.faces) == 0:
            problems.append(f"{ob.name} has no faces")
        bm.free()
        ev.to_mesh_clear()
    if math.isinf(lo[0]):
        raise SystemExit("the model has no geometry: every part is empty")
    size = [hi[i] - lo[i] for i in range(3)]
    return {"bbox_min": lo, "bbox_max": hi, "size_cm": [round(100 * s, 2) for s in size], "parts": info,
            "problems": problems}


QUALITY = {"preview": dict(size=(360, 480), samples=32), "final": dict(size=(600, 800), samples=160)}
DEFAULT_VIEWS = {   # name: (azimuth degrees right of the front, elevation degrees, lens mm)
    "front": (0, 8, 70), "three_quarter": (-35, 25, 50), "right": (90, 8, 70), "back": (180, 15, 60),
    "top": (0, 88, 60),
}


def stage(bbox_min, bbox_max, quality):
    """Dim warm studio: a large floor, a key, fill and rim light scaled to the object, Cycles on the CPU."""
    scene = bpy.context.scene
    lo, hi = Vector(bbox_min), Vector(bbox_max)
    diag = max((hi - lo).length, 0.01)
    centre = (lo + hi) / 2
    floor = bpy.data.meshes.new("floor")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=diag * 12)
    bm.to_mesh(floor)
    bm.free()
    floor_ob = bpy.data.objects.new("floor", floor)
    scene.collection.objects.link(floor_ob)
    floor.materials.append(material("floor", (0.20, 0.17, 0.13), 0.55))
    # tuned on a 23 cm bottle (bounding-box diagonal 0.26 m, lights 0.637 m away); for other sizes the lights
    # keep their distance relative to the object and their power grows with the square of that distance
    for name, direction, power, size, color in (("key", (-0.30, -0.35, 0.44), 6.0, 0.35, (1.0, 0.95, 0.88)),
                                                ("fill", (0.45, -0.20, 0.14), 2.3, 0.5, (0.9, 0.93, 1.0)),
                                                ("rim", (0.10, 0.28, 0.29), 16.0, 0.25, (1.0, 0.85, 0.6))):
        dist = 2.45 * diag
        light = bpy.data.lights.new(name, "AREA")
        light.energy = power * (dist / 0.637) ** 2
        light.size = size * diag / 0.26
        light.color = color
        ob = bpy.data.objects.new(name, light)
        scene.collection.objects.link(ob)
        ob.location = centre + Vector(direction).normalized() * dist
        ob.rotation_euler = (centre - ob.location).to_track_quat("-Z", "Y").to_euler()
    world = bpy.data.worlds.new("world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.20, 0.19, 0.17, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.2
    scene.world = world
    q = QUALITY[quality]
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = q["samples"]
    scene.cycles.use_denoising = True          # no effect in builds without OpenImageDenoise (Ubuntu's)
    scene.cycles.max_bounces = 24
    scene.cycles.transmission_bounces = 16
    scene.cycles.transparent_max_bounces = 16
    scene.cycles.glossy_bounces = 8
    scene.cycles.caustics_reflective = False   # caustics and rare bright samples cause most of the grain
    scene.cycles.caustics_refractive = False
    scene.cycles.blur_glossy = 1.0
    scene.cycles.sample_clamp_indirect = 3.0
    scene.render.resolution_x, scene.render.resolution_y = q["size"]
    scene.view_settings.view_transform = "AgX"
    return floor_ob


def frame_camera(cam, bbox_min, bbox_max, azimuth, elevation, lens, aspect):
    """Place the camera so that the whole bounding box fills most of the frame from the given direction."""
    lo, hi = Vector(bbox_min), Vector(bbox_max)
    centre = (lo + hi) / 2
    radius = max((hi - lo).length / 2, 0.005)
    cam.data.lens = lens
    cam.data.sensor_fit = "AUTO"
    fov_long = 2 * math.atan(18.0 / lens)                     # 36 mm sensor on the long side
    fov_short = 2 * math.atan(math.tan(fov_long / 2) * min(aspect, 1 / aspect))
    dist = radius / math.sin(fov_short / 2) * 1.05
    az, el = math.radians(azimuth), math.radians(elevation)
    direction = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    cam.location = centre + direction * dist
    cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()


def render_views(out_dir, views, bbox_min, bbox_max, clay=False, hide_in_clay=()):
    scene = bpy.context.scene
    os.makedirs(out_dir, exist_ok=True)
    cam = bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    aspect = scene.render.resolution_x / scene.render.resolution_y
    hidden = []
    if clay:
        scene.view_layers[0].material_override = material("clay", (0.70, 0.70, 0.70), 0.6)
        for ob in scene.objects:
            if ob.name in hide_in_clay or ob.get("open_ok"):
                ob.hide_render = True
                hidden.append(ob)
    paths = {}
    for name, (azimuth, elevation, lens) in views.items():
        frame_camera(cam, bbox_min, bbox_max, azimuth, elevation, lens, aspect)
        path = os.path.join(out_dir, f"{name}{'_clay' if clay else ''}.png")
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        paths[name] = path
        print(f"rendered {path}", flush=True)
    scene.view_layers[0].material_override = None
    for ob in hidden:
        ob.hide_render = False
    bpy.data.objects.remove(cam)
    return paths


def export_print_parts(out_dir, groups):
    """3D-printing export: each group {name: [part objects]} becomes one solid, written as out_dir/name.stl in mm.

    The parts of a group are joined with an exact boolean union, so overlapping pieces (bars sunk into a rim)
    become one closed shell. Returns per group: file, faces, open edges (must be 0), volume and size.
    """
    os.makedirs(out_dir, exist_ok=True)
    deps = bpy.context.evaluated_depsgraph_get()
    report = {}
    for group, members in groups.items():
        copies = []
        for ob in members:
            me = bpy.data.meshes.new_from_object(ob.evaluated_get(deps))
            me.transform(ob.matrix_world)
            cp = bpy.data.objects.new(f"{group}_{ob.name}", me)
            bpy.context.scene.collection.objects.link(cp)
            copies.append(cp)
        # join every piece into one mesh, then let the exact boolean resolve where they cross (a self-union):
        # a union with a collection only merges the pieces that touch the first one
        for o in bpy.context.selected_objects:
            o.select_set(False)
        for cp in copies:
            cp.select_set(True)
        target = copies[0]
        bpy.context.view_layer.objects.active = target
        if len(copies) > 1:
            bpy.ops.object.join()
        coll = bpy.data.collections.new(f"{group}_empty")
        mod = target.modifiers.new("self_union", "BOOLEAN")
        mod.operation = "UNION"
        mod.operand_type = "COLLECTION"
        mod.collection = coll
        mod.solver = "EXACT"
        mod.use_self = True
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.collections.remove(coll)
        target.select_set(False)
        bm = bmesh.new()
        bm.from_mesh(target.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
        bm.to_mesh(target.data)
        open_edges = sum(1 for e in bm.edges if not e.is_manifold)
        volume = abs(bm.calc_volume())
        xs, ys, zs = zip(*[v.co[:] for v in bm.verts])
        shells = _count_shells(bm)
        bm.free()
        for o in bpy.context.selected_objects:
            o.select_set(False)
        target.select_set(True)
        path = os.path.join(out_dir, f"{group}.stl")
        bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, global_scale=1000.0, apply_modifiers=True)
        target.select_set(False)
        report[group] = {"file": path, "faces": len(target.data.polygons), "open_edges": open_edges, "shells": shells,
                         "volume_cm3": round(volume * 1e6, 2),
                         "size_mm": [round(1000 * (max(c) - min(c)), 1) for c in (xs, ys, zs)]}
        bpy.data.objects.remove(target)
    return report


def _count_shells(bm):
    """Number of separate connected pieces in a mesh (a printed part should be 1)."""
    seen, shells = set(), 0
    for f in bm.faces:
        if f.index in seen:
            continue
        shells += 1
        stack = [f]
        seen.add(f.index)
        while stack:
            face = stack.pop()
            for e in face.edges:
                for other in e.link_faces:
                    if other.index not in seen:
                        seen.add(other.index)
                        stack.append(other)
    return shells


def export(out_dir, parts, name="model"):
    for ob in bpy.context.scene.objects:
        ob.select_set(ob in parts)
    glb = os.path.join(out_dir, f"{name}.glb")
    bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=True, export_apply=True)
    obj = os.path.join(out_dir, f"{name}.obj")
    bpy.ops.wm.obj_export(filepath=obj, export_selected_objects=True, apply_modifiers=True, export_materials=True,
                          path_mode="COPY", forward_axis="NEGATIVE_Z", up_axis="Y")
    for ob in parts:
        ob.select_set(False)
    return glb, obj
