"""Ceiling mount for a Canon LS-88Hi III calculator, keys facing down - from photos/photo_01..05.jpg.

Metres; Z up; front (the calculator's keypad end) faces -Y. The scene is built the way the mount prints and the
way the photos show the calculator: mount plate on z = 0, calculator lying in it keys up. On the ceiling the
whole thing is turned over: the plate is screwed to the ceiling and the keys face the floor.
Run: model3d build THIS_FOLDER [--final]

Mount: a plate with two countersunk screw holes (under the calculator), low side rails, an end wall with a lip
that holds the raised display end, and a separate turn button at the keypad end. To fit: lay the calculator in,
push it towards the end wall so the display end goes under the lip, then turn the button over the keypad end.
"""
import math

MM = 0.001
DIMS = {   # millimetres here; build() converts
    # the calculator
    "calc_length": 143.0,        # given by Canon's spec: 143 x 89.5 x 25 mm, 90 g
    "calc_width": 89.5,          # Canon spec
    "calc_height": 25.0,         # Canon spec: table to the top of the raised display end
    "calc_thickness": 9.0,       # est photo_01 (8.7 mm at 9.2 px/mm, including any feet)
    "flat_length": 85.0,         # est photo_02, photo_04: keypad end to the bend underneath
    "bend_deg": 16.0,            # est photo_02 + spec height: the display section's tilt
    # the mount
    "plate": 3.0,                # plate thickness
    "side_clear": 0.4,           # gap between the calculator and each side rail
    "end_clear": 0.6,            # gap between the display end and the end wall, and under the lip
    "lip": 3.0,                  # how far the lip reaches over the display end's face
    "wall": 3.0,                 # end wall thickness
    "rail": 2.4,                 # side rail thickness
    "rail_height": 5.0,          # above the calculator's underside
    "load_gap": 4.0,             # room at the keypad end to lay the calculator in before sliding it under the lip
    "boss_radius": 5.0,          # post that carries the turn button
    "button_clear": 0.4,         # gap between the turn button and the calculator's face
    "button_reach": 5.0,         # how far the turn button reaches over the keypad end
    "screw_hole": 4.5,           # countersunk ceiling screws, 4 mm
    "screw_head": 8.8,
    "pilot_hole": 2.5,           # for an M3 (3 mm) self-tapping screw: the turn button's pivot
}

ASSUMPTIONS = [
    "Calculator size from Canon's specification (143 x 89.5 x 25 mm); not measured. Thickness at the keypad end "
    "(9 mm), where the underside bends (85 mm from the keypad end) and the bend angle (16 degrees) are read off "
    "the photos. These decide the fit: measure them before printing.",
    "Underside flat in the keypad section (no tall feet).",
    "Fixed with two 4 mm countersunk screws (plugs to suit the ceiling); the turn button pivots on an M3 x 16 "
    "self-tapping screw.",
]

VIEWS = {   # name -> (azimuth right of the front, elevation, lens mm); one per photo
    "photo_01": (0, 10, 35),
    "photo_02": (-90, 12, 35),
    "photo_03": (180, 18, 35),
    "photo_04": (90, 12, 35),
    "photo_05": (0, 75, 35),
}

PRINT_PARTS = {"mount": ["mount"], "turn_button": ["turn_button"]}


def build(lib):
    from mathutils import Matrix, Vector
    from mathutils.bvhtree import BVHTree
    d = DIMS
    T = math.tan(math.radians(d["bend_deg"]))
    c, s = math.cos(math.radians(d["bend_deg"])), math.sin(math.radians(d["bend_deg"]))
    t, P, L = d["calc_thickness"], d["plate"], d["calc_length"]
    W2 = d["calc_width"] / 2
    Y0 = -L / 2                                  # world y of the keypad end

    mount_mat = lib.preset("plastic", "mount_pla", color=lib.color("#e8772e"), roughness=0.45)
    body_mat = lib.preset("plastic", "calc_body", color=lib.photo_color("photos/photo_05.jpg", (0.30, 0.775, 0.60, 0.80)))
    white = lib.preset("plastic", "key_white", color=lib.color("#e9e6de"))
    blue = lib.preset("plastic", "key_blue", color=lib.color("#7fa9b6"))
    red = lib.preset("plastic", "key_red", color=lib.color("#d65a62"))
    lcd = lib.material("lcd", color=lib.color("#8e9389"), roughness=0.25)
    solar = lib.material("solar", color=lib.color("#2a2a2c"), roughness=0.3)
    ink = lib.material("ink", color=lib.color("#2e3a4a"), roughness=0.5)

    def at(u, h):
        """(distance from the keypad end, height above the plate) -> world (y, z) in mm."""
        return Y0 + u, P + h

    def prism_x(name, pts, x0, x1, mat, bevel=0.0):
        """Prism from a side profile [(u, h), ...] running from x0 to x1."""
        ob = lib.extrude(name, pts, x0, x1, mat, bevel=bevel, segments=2)
        ob.data.transform(Matrix(((0, 0, 1, 0), (1, 0, 0, Y0), (0, 1, 0, P), (0, 0, 0, 1))))
        return ob

    # ---- the calculator (reference, not printed): a plate bent up 16 degrees under the display
    bend = d["flat_length"]
    ls = (L - bend) / c                           # slope length that makes the overall length L
    C = (bend + ls * c, ls * s)                   # far bottom corner
    D = (C[0] - t * s, C[1] + t * c)              # far top corner (the end face is square to the slope)
    k = t * (1 - c) / s                           # top surface bends where the offset slope meets z = t
    E = (bend + k * c - t * s, t)
    profile = [(0, 0), (bend, 0), C, D, E, (0, t)]
    body = prism_x("calc_body", profile, -W2, W2, body_mat, bevel=1.0)
    calc = [body]

    rows = [71.5, 60.0, 47.3, 34.3, 21.3]         # est photo_05, key centres from the keypad end
    cols = [-32.0, -16.0, 0.0, 16.0, 32.0]
    for r, u in enumerate(rows):
        for q, x in enumerate(cols):
            if q == 3 and r == 4:
                continue                          # the tall + key covers rows 3 and 4
            depth = 8.0 if r == 0 else 9.5
            uc = u
            if q == 3 and r == 3:
                depth, uc = 22.5, (rows[3] + rows[4]) / 2
            mat = (red if q < 2 else blue) if r == 0 else (blue if q >= 3 else white)
            y, z = at(uc, t + 1.0)
            calc.append(lib.rounded_box(f"key_{r}{q}", (13.0, depth, 3.0), (x, y, z), 1.2, mat))

    def on_slope(ob):
        """Turn a part built flat at height t (just past the bend) up onto the display section."""
        y, z = at(E[0], t)
        return lib.transform(ob, rotate_deg=(d["bend_deg"], 0, 0), about=(0, y, z))

    y, z = at(E[0] + 17.0, t)
    calc.append(on_slope(lib.rounded_box("display", (73.0, 24.0, 0.6), (0, y, z), 0.25, lcd)))
    y, z = at(E[0] + 50.0, t)
    calc.append(on_slope(lib.rounded_box("solar", (22.0, 10.0, 0.6), (22.0, y, z), 0.25, solar)))
    calc.append(on_slope(lib.text_mesh("canon", "Canon", 7.0, 0.4, (-24.0, y, z), ink)))

    # ---- the mount: plate, side rails, end wall with lip, boss for the turn button
    g = d["end_clear"]
    n = (c, s)                                    # outward normal of the display end face
    Ci = (C[0] + g * n[0], C[1] + g * n[1])       # wall's inner face: the end face moved out by the gap
    def u_in(h):
        return Ci[0] + (Ci[1] - h) * T
    lip_low = D[1] + g
    lip_top = lip_low + 2.5
    lip_in = D[0] - d["lip"]
    wall_out = lambda h: u_in(h) + d["wall"] / c
    xo = W2 + d["side_clear"] + d["rail"]
    wall = prism_x("end_wall", [(u_in(-1), -1), (wall_out(-1), -1), (wall_out(lip_top), lip_top),
                                (lip_in, lip_top), (lip_in, lip_low), (u_in(lip_low), lip_low)], -xo, xo, mount_mat)
    u_front = -d["load_gap"] - 2 * d["boss_radius"] - 2.0
    u_back = wall_out(-1) + 0.6                 # plate edges stand clear of the wall and rail faces (no coplanar unions)
    y, _ = at((u_front + u_back) / 2, 0)
    plate = lib.rounded_box("mount", (2 * xo + 1.2, u_back - u_front, P), (0, y, P / 2), 1.2, mount_mat)
    rh = d["rail_height"]
    hx = (rh + (u_in(0) + 1.5 - bend) * T) / (1 + T * T)          # where the rail's sloping top meets the wall
    rail_pts = [(0, -0.5), (u_in(0) + 1.5, -0.5), (u_in(hx) + 1.5, hx), (bend, rh), (0, rh)]
    rails = [prism_x(f"rail_{i}", rail_pts, x0, x0 + d["rail"], mount_mat)
             for i, x0 in enumerate((-xo, W2 + d["side_clear"]))]
    pivot_u = -d["load_gap"] - d["boss_radius"]
    boss_top = t + d["button_clear"]
    y, _ = at(pivot_u, 0)
    boss = lib.cylinder("boss", d["boss_radius"], boss_top + 0.5, (0, y, P + boss_top / 2 - 0.25), mount_mat)
    for part in [wall, boss] + rails:
        lib.boolean(plate, part, "UNION")

    # holes: two countersunk ceiling screws under the keypad section, the pilot hole for the pivot screw,
    # and a window under the display section (nothing rests there)
    for u in (22.0, 66.0):
        y, _ = at(u, 0)
        lib.boolean(plate, lib.cylinder("screw", d["screw_hole"] / 2, 3 * P, (0, y, P / 2), None))
        rt = d["screw_head"] / 2 + 0.05
        depth = rt - d["screw_hole"] / 2
        lib.boolean(plate, lib.cylinder("sink", d["screw_hole"] / 2, depth, (0, y, P + 0.05 - depth / 2), None,
                                        radius_top=rt))
    y, _ = at(pivot_u, 0)
    lib.boolean(plate, lib.cylinder("pilot", d["pilot_hole"] / 2, 11.0, (0, y, P + boss_top - 5.4), None))
    y, _ = at((bend + 7 + lip_in - 1) / 2, 0)
    lib.boolean(plate, lib.rounded_box("window", (2 * W2 - 18, lip_in - 1 - bend - 7, 30), (0, y, P / 2), 4.0, None))
    mount = plate

    # ---- turn button: disc on the boss, a tongue over the keypad end, a tooth that stops the calculator
    # sliding back out from under the lip, and a grip tab
    y_piv, z_b = at(pivot_u, boss_top)
    reach = d["button_reach"]
    button = lib.cylinder("turn_button", 6.0, 3.0, (0, y_piv, z_b + 1.5), mount_mat)
    u0, u1 = pivot_u - 14.0, reach
    y, _ = at((u0 + u1) / 2, 0)
    lib.boolean(button, lib.rounded_box("tongue", (10.0, u1 - u0, 3.0), (0, y, z_b + 1.5), 1.0, mount_mat), "UNION")
    r_out = -pivot_u - d["button_clear"]           # outer face: an arc round the pivot, so it never swings into the calculator
    r_in = d["boss_radius"] + 0.6
    tooth_h = boss_top - 0.6
    tooth = lib.cylinder("tooth", r_out, tooth_h + 0.3, (0, y_piv, P + 0.6 + (tooth_h + 0.3) / 2), mount_mat, segments=96)
    lib.boolean(tooth, lib.cylinder("tooth_in", r_in, 40, (0, y_piv, P), None, segments=96))
    lib.boolean(tooth, lib.rounded_box("tooth_box", (8.0, r_out + 1, 40), (0, y_piv + (r_out + 1) / 2, P), 0, None),
                "INTERSECT")
    lib.boolean(button, tooth, "UNION")
    lib.boolean(button, lib.cylinder("pivot", 1.7, 20, (0, y_piv, z_b), None))

    # ---- fit checks (mm): installed, while turning the button, and the path in (tilted under the lip)
    def tree(ob, m=Matrix.Identity(4)):
        return BVHTree.FromPolygons([m @ v.co for v in ob.data.vertices], [p.vertices[:] for p in ob.data.polygons])
    lift = Matrix.Translation((0, 0, 0.05))       # resting on the plate is contact, not a clash
    t_mount, t_body = tree(mount), tree(body, lift)
    piv = Vector((0, y_piv, 0))
    turn = lambda a: Matrix.Translation(piv) @ Matrix.Rotation(math.radians(a), 4, "Z") @ Matrix.Translation(-piv)
    print("FIT installed: mount touches calculator:", bool(t_mount.overlap(t_body)),
          "| button touches calculator:", bool(tree(button).overlap(t_body)))
    hits = [a for a in range(0, 91, 5) if tree(button, turn(a)).overlap(t_body)]
    print("FIT turning the button 0-90 deg: hits at", hits or "none")
    t_off = tree(button, turn(90))
    shift = 1.5
    yD, zD = at(D[0] - shift, D[1])
    pD = Vector((0, yD, zD))
    bad = []
    for i in range(0, 41):
        phi = i * 0.5
        m = (Matrix.Translation(pD) @ Matrix.Rotation(-math.radians(phi), 4, "X") @ Matrix.Translation(-pD)
             @ Matrix.Translation((0, -shift, 0)) @ lift)
        tb = tree(body, m)
        if t_mount.overlap(tb) or t_off.overlap(tb):
            bad.append(phi)
    print(f"FIT path in (display end {shift} mm short of home, tilted 0-20 deg about the lip): hits at", bad or "none")
    print(f"FIT lip over the display end: {d['lip']} mm; button over the keypad end: {reach} mm; "
          f"play along the length: {g + d['button_clear']:.1f} mm")
    print(f"FIT calculator: length {C[0]:.1f} mm, top of display end {D[1]:.1f} mm, "
          f"mount {2 * xo:.1f} x {u_back - u_front:.1f} x {P + lip_top:.1f} mm")

    parts = [mount, button] + calc
    for ob in parts:
        ob.data.transform(Matrix.Scale(MM, 4))
        ob.data.update()
    return parts
