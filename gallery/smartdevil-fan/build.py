"""SMARTDEVIL USB desk fan (stepless dial) - from photos/photo_01..05.jpg, for display and 3D printing.

Metres; Z up; the fan stands on z = 0 centred on the Z axis; its front (grille with the logo, dial) faces -Y.
The head is built in its own frame (axis = +Z, front = +Z) and then turned and lifted onto the base.
Run: model3d build THIS_FOLDER [--final]
"""
import math

MM = 0.001
DIMS = {   # millimetres here; build() converts
    "housing_radius": 72.5,      # listing: 145 mm wide
    "housing_depth": 79.0,       # est photo_02
    "barrel_bulge": 2.0,         # est: the outside bulges this much in the middle
    "opening_radius": 62.0,      # est photo_05
    "head_bottom": 31.0,         # est photo_02: lowest point of the head above the table
    "front_hub_radius": 21.5,    # est photo_05
    "front_bars": 36,            # est photo_05 (round 2: denser than first read)
    "front_sweep_deg": 110.0,    # est photo_05: how far each front bar turns from hub to rim
    "rear_hub_radius": 25.0,     # est photo_03
    "rear_bars": 40,             # est photo_03 (round 2)
    "rear_sweep_deg": -12.0,     # est photo_03: nearly radial spokes (round 2)
    "rear_dome": 8.0,            # est photo_01, photo_02
    "bar_width": 2.0,            # printable: at least 4 nozzle widths
    "bar_depth": 4.0,
    "blades": 5,                 # listing
    "blade_pitch_deg": 30.0,     # est
    "blade_thickness": 1.6,
    "base_radius": 36.0,         # est photo_02 (level side view: 72 mm across; round 2)
    "base_height": 36.0,         # est photo_02
    "dial_radius": 6.5,          # est photo_04
    "dial_reach": 9.0,           # est photo_04: how far it sticks out of the base
    "dial_offset_x": 9.0,        # est photo_05: right of centre
    "dial_z": 29.0,              # est photo_02, photo_04
    "fit_clearance": 0.2,        # printing: gap between the front grille and the housing bore
}

ASSUMPTIONS = [
    "Scale from a retail listing of the SmartDevil stepless-dial desk fan (17.3 x 14.5 x 9.8 cm), the closest "
    "match found; not measured. Model: 17.6 cm tall, 14.5 cm wide, about 8.9 cm deep (the listing says 9.8).",
    "Head upright; the real head tilts up to 20 degrees.",
    "Bar counts, bar curves and blade shape read off the photos and simplified.",
    "Printed as four parts (base, housing with rear grille, front grille, rotor); a display model with no motor.",
]

VIEWS = {   # name -> (azimuth right of the front, elevation, lens mm); one per photo
    "photo_05": (0, 18, 35),
    "photo_02": (90, 6, 35),
    "photo_03": (180, 15, 35),
    "photo_04": (-90, 8, 35),
    "photo_01": (0, 85, 35),
}

PRINT_PARTS = {
    "base": ["base", "dial"],
    "housing": ["housing", "rear_rim", "rear_hub"] + [f"rear_bar_{i:02d}" for i in range(DIMS["rear_bars"])],
    "front_grille": ["front_rim", "front_hub", "logo"] + [f"front_bar_{i:02d}" for i in range(DIMS["front_bars"])],
    "rotor": ["rotor_hub", "axle"] + [f"blade_{i}" for i in range(DIMS["blades"])],
}


def build(lib):
    d = DIMS
    black = lib.preset("plastic", "black_plastic", color=lib.color("#1d1d1f"), roughness=0.55)
    dial_mat = lib.preset("plastic", "dial_plastic", color=lib.color("#202024"), roughness=0.3)
    logo_mat = lib.preset("plastic", "logo_print", color=lib.color("#d8cfc4"), roughness=0.5)
    parts = []

    R, L, Ri = d["housing_radius"], d["housing_depth"], d["opening_radius"]
    zc = d["head_bottom"] + R                       # height of the head's centre (mm)

    def head(ob):
        """Head frame (axis +Z = front) -> world: front to -Y, lifted onto the base; mm -> m."""
        ob.data.transform(__import__("mathutils").Matrix.Scale(MM, 4))
        return lib.transform(ob, rotate_deg=(90, 0, 0), move=(0, 0, zc * MM))

    def mm(points):
        return [tuple(c * MM for c in p) for p in points]

    # ---- housing: a thick ring; barrel-shaped outside with a seam, stepped front bezel, rounded back edge
    half = L / 2
    barrel = []
    for k in range(29):
        a = -34 + (31 + 34) * k / 28
        r = R - d["barrel_bulge"] + d["barrel_bulge"] * (1 - (a / 34) ** 2)
        if abs(a) < 0.5:
            r -= 0.4                                # moulding seam
        barrel.append((r, a))
    ring = [(Ri, -half), (65.0, -half)] + lib.arc(65.0, -34.0, 5.5, -90, 0, 6)[:-1] + barrel
    ring += [(69.0, 31.5), (69.0, half - 1)] + lib.arc(68.0, half - 1, 1.0, 0, 90, 3) + [(Ri, half), (Ri, -half)]
    parts.append(head(lib.lathe("housing", ring, black)))

    # ---- front grille: rim that drops into the bore, spiral bars, hub disc with the raised logo
    fz0, fz1 = half - 2.5 - d["bar_depth"], half - 2.5
    rim_out = Ri - d["fit_clearance"]
    parts.append(head(lib.lathe("front_rim", [(rim_out - 1.8, fz0), (rim_out, fz0), (rim_out, fz1),
                                              (rim_out - 1.8, fz1), (rim_out - 1.8, fz0)], black)))
    for i in range(d["front_bars"]):
        a0 = 360.0 * i / d["front_bars"]
        pts = []
        for k in range(25):
            s = k / 24
            r = d["front_hub_radius"] - 1 + (rim_out - 1.0 - d["front_hub_radius"] + 1) * s
            th = math.radians(a0 - d["front_sweep_deg"] * s ** 0.8)
            pts.append((r * math.cos(th), r * math.sin(th), (fz0 + fz1) / 2))
        parts.append(head(lib.ribbon(f"front_bar_{i:02d}", pts, d["bar_depth"], d["bar_width"], black)))   # mm; head() scales
    hub = lib.cylinder("front_hub", d["front_hub_radius"] * MM, (fz1 + 0.8 - fz0) * MM,
                       (0, 0, (fz0 + fz1 + 0.8) / 2 * MM), black)
    parts.append(lib.transform(hub, rotate_deg=(90, 0, 0), move=(0, 0, zc * MM)))
    logo = lib.text_mesh("logo", "SMARTDEVIL", 5.0 * MM, 0.8 * MM, (0, 0, (fz1 + 0.8) * MM), logo_mat)
    parts.append(lib.transform(logo, rotate_deg=(90, 0, 0), move=(0, 0, zc * MM)))   # 0.4 mm proud of the hub

    # ---- rear grille: rim inside the back of the bore, curved bars domed out behind, big hub disc
    parts.append(head(lib.lathe("rear_rim", [(Ri - 2.0, -half - 0.5), (Ri + 0.3, -half - 0.5), (Ri + 0.3, -half + 2.5),
                                             (Ri - 2.0, -half + 2.5), (Ri - 2.0, -half - 0.5)], black)))
    back = -half - d["rear_dome"]                   # centre of the dome, behind the back face
    for i in range(d["rear_bars"]):
        a0 = 360.0 * i / d["rear_bars"]
        pts = []
        for k in range(21):
            s = k / 20
            r = d["rear_hub_radius"] - 1 + (Ri - 1.0 - d["rear_hub_radius"] + 1) * s
            z = back + (d["rear_dome"] + 1.0) * s ** 1.6
            th = math.radians(a0 + d["rear_sweep_deg"] * s)
            pts.append((r * math.cos(th), r * math.sin(th), z))
        parts.append(head(lib.ribbon(f"rear_bar_{i:02d}", pts, d["bar_depth"], d["bar_width"], black)))   # mm; head() scales
    rh = lib.cylinder("rear_hub", d["rear_hub_radius"] * MM, 4.4 * MM, (0, 0, back * MM), black)
    parts.append(lib.transform(rh, rotate_deg=(90, 0, 0), move=(0, 0, zc * MM)))

    # ---- rotor: hub, axle back to the rear hub (glue point), five pitched blades
    rz = 14.0                                       # axial centre of the blades
    hubr = lib.cylinder("rotor_hub", 16.0 * MM, 16.0 * MM, (0, 0, rz * MM), black)
    parts.append(lib.transform(hubr, rotate_deg=(90, 0, 0), move=(0, 0, zc * MM)))
    axle_end = back + 2.2 + 0.1                     # stops at the rear hub's front face: the printed parts must not overlap
    axle = lib.cylinder("axle", 4.0 * MM, (rz - axle_end) * MM, (0, 0, (rz + axle_end) / 2 * MM), black)
    parts.append(lib.transform(axle, rotate_deg=(90, 0, 0), move=(0, 0, zc * MM)))
    for i in range(d["blades"]):
        edge_lead, edge_trail = [], []
        for k in range(17):
            s = k / 16
            r = 14.0 + (57.0 - 14.0) * s
            w = math.radians(16 + 16 * s)           # half the blade's angular width
            c = math.radians(22 * s * s)            # the blade sweeps forward towards the tip
            edge_lead.append((r * math.cos(c + w), r * math.sin(c + w)))
            edge_trail.append((r * math.cos(c - w), r * math.sin(c - w)))
        outline = edge_trail + list(reversed(edge_lead))
        t = d["blade_thickness"] / 2
        blade = lib.extrude(f"blade_{i}", mm(outline), -t * MM, t * MM, black, bevel=0.3 * MM, segments=2)
        lib.transform(blade, rotate_deg=(d["blade_pitch_deg"], 0, 360.0 * i / d["blades"]))
        blade.data.transform(__import__("mathutils").Matrix.Translation((0, 0, rz * MM)))
        parts.append(lib.transform(blade, rotate_deg=(90, 0, 0), move=(0, 0, zc * MM)))

    # ---- base: cylinder, groove, upper section with a saddle for the head, USB-C port at the back
    br, bh = d["base_radius"], d["base_height"]
    prof = [(0, 0), (br - 1.5, 0)] + lib.arc(br - 1.5, 1.5, 1.5, -90, 0, 3) + [(br, 19.0)] + lib.arc(br - 1, 19.0, 1, 0, 90, 2)
    prof += [(br - 2.2, 20.5), (br - 2.2, 22.0), (br - 0.5, 23.0), (br - 0.5, bh - 2)] + lib.arc(br - 2.5, bh - 2, 2, 0, 90, 3)
    prof += [(0, bh)]
    base = lib.lathe("base", mm(prof), black)
    saddle = lib.cylinder("saddle", (R + 0.3) * MM, 120 * MM, (0, 0, zc * MM), None, axis="Y", segments=128)
    lib.boolean(base, saddle)
    port = lib.rounded_box("port", (9.0 * MM, 14 * MM, 3.2 * MM), (0, br * MM, 5.0 * MM), 1.4 * MM, None)
    lib.boolean(base, port)
    parts.append(base)

    # ---- dial at the front of the upper section, right of centre, with an engraved index line
    x = d["dial_offset_x"]
    y_surface = -math.sqrt((br - 0.5) ** 2 - x * x)
    y0, y1 = y_surface + 3.0, y_surface - d["dial_reach"]          # sunk 3 mm into the base
    dial = lib.cylinder("dial", d["dial_radius"] * MM, (y0 - y1) * MM, (x * MM, (y0 + y1) / 2 * MM, d["dial_z"] * MM),
                        dial_mat, axis="Y")
    line = lib.rounded_box("index", (0.8 * MM, 1.2 * MM, 5.0 * MM), (x * MM, y1 * MM, (d["dial_z"] + 3.0) * MM),
                           0.2 * MM, None)
    lib.boolean(dial, line)
    parts.append(dial)
    return parts
