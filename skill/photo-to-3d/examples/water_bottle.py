"""Clear "SPORT" water bottle with a white flip-top lid - built from photos/photo_01.jpg.

Metres; Z up; the bottle stands on z = 0 centred on the Z axis; its front (latch side up, strap loop)
faces -Y. Run: model3d build THIS_FOLDER [--final]
"""

DIMS = {
    "body_radius": 0.034,          # est: 6.8 cm across, typical for a 600 ml bottle; the photo's proportions agree
    "wall": 0.0022,                # est
    "base": 0.007,                 # est: thick moulded bottom seen in the photo
    "bottom_fillet": 0.007,        # est
    "shoulder_z": 0.172,           # est: body steps in to the threaded neck, hidden by the lid
    "neck_radius": 0.030,          # est
    "neck_top": 0.197,             # est
    "water_level": 0.150,          # est
    "lid_radius": 0.0348,          # est: white lid, lower ring
    "lid_bottom": 0.176,           # est: lid is about a fifth of the height in the photo
    "lid_seam": 0.203,             # est
    "cap_radius": 0.0336,          # est
    "cap_top": 0.2245,             # est
    "cover_size": (0.066, 0.026, 0.007),    # est: flip cover across the top
    "window_size": (0.042, 0.018, 0.0015),  # est: clear window in the cover
    "latch_size": (0.004, 0.018, 0.020),    # est: tab down the left side of the cap
    "hinge_radius": 0.0035,        # est
    "band_z": (0.160, 0.171),      # est: clear strap band under the lid
    "band_thickness": 0.0015,      # est
    "loop_size": (0.028, 0.026),   # est: strap loop at the front, width x reach
    "loop_droop_deg": 28.0,        # est
    "straw_radius": 0.0035,        # est
    "straw_angle_deg": 55.0,       # est: straw seen right of the print
    "straw_offset": 0.022,         # est
    "print_z": (0.032, 0.106),     # est: "SPORT" runs down the lower two thirds
    "print_height": 0.017,         # est
    "print_angle_deg": 8.0,        # est: just right of the front
}

ASSUMPTIONS = [
    "No sizes given: 23 cm tall and 6.8 cm across, typical of a 600 ml flip-top bottle.",
    "Water filled to 15 cm.",
    "Flip cover simplified to a rounded block with a clear window; the real one is a larger hood with a "
    "patterned insert.",
    "Print in DejaVu Sans; the real lettering is thinner and rounder.",
]

VIEWS = {   # name -> (azimuth right of the front, elevation, lens mm)
    "photo_01": (-15, 37, 42),     # the direction photo_01 was taken from
    "front": (0, 8, 70),
    "back_right": (135, 25, 42),
    "top": (0, 88, 60),
}


def build(lib):
    import math
    d = DIMS
    mats = {
        "clear": lib.preset("clear_plastic"),
        "water": lib.preset("water"),
        "white": lib.preset("plastic", "white_plastic", color=(0.86, 0.86, 0.84)),
        "window": lib.see_through("clear_window"),
        "strap": lib.preset("frosted", "strap_plastic", roughness=0.28),
        "straw": lib.preset("frosted", "straw", color=(0.93, 0.93, 0.93), roughness=0.32, transmission=0.55),
    }
    R, t, base, rb = d["body_radius"], d["wall"], d["base"], d["bottom_fillet"]
    rbi = rb - t / 2
    parts = []

    # clear body: outside from the bottom centre up to the neck lip, then the inside back down
    prof = [(0.0, 0.0015), (0.013, 0.0015), (0.015, 0.0), (R - rb, 0.0)]
    prof += lib.arc(R - rb, rb, rb, -90, 0)
    prof += [(R, d["shoulder_z"])] + lib.arc(R - 0.004, d["shoulder_z"], 0.004, 0, 60, 4)
    prof += [(d["neck_radius"], d["shoulder_z"] + 0.004), (d["neck_radius"], d["neck_top"]),
             (d["neck_radius"] - 0.0028, d["neck_top"]), (d["neck_radius"] - 0.0028, d["shoulder_z"] + 0.003),
             (R - t, d["shoulder_z"] - 0.002), (R - t, base + rbi)]
    prof += lib.arc(R - t - rbi, base + rbi, rbi, 0, -90)
    prof += [(0.0, base)]
    parts.append(lib.lathe("body", prof, mats["clear"]))

    # water, a hair inside the body so the two surfaces do not touch
    gap, wl = 0.0002, d["water_level"]
    prof = [(0.0, base + gap), (R - t - rbi, base + gap)]
    prof += lib.arc(R - t - rbi, base + rbi, rbi - gap, -90, 0)
    prof += [(R - t - gap, wl), (0.0, wl)]
    parts.append(lib.lathe("water", prof, mats["water"]))

    # white lid: lower ring with a seam, upper cap with a rounded top
    lr, cr, f = d["lid_radius"], d["cap_radius"], 0.0015
    prof = [(0.0, d["neck_top"] + 0.001), (d["neck_radius"] + 0.0002, d["neck_top"] + 0.001),
            (d["neck_radius"] + 0.0002, d["lid_bottom"]), (lr - f, d["lid_bottom"])]
    prof += lib.arc(lr - f, d["lid_bottom"] + f, f, -90, 0, 4)
    prof += [(lr, d["lid_seam"] - f)] + lib.arc(lr - f, d["lid_seam"] - f, f, 0, 60, 3)
    prof += [(cr - 0.0004, d["lid_seam"] + 0.0004), (cr, d["lid_seam"] + 0.0008), (cr, d["cap_top"] - 0.003)]
    prof += lib.arc(cr - 0.003, d["cap_top"] - 0.003, 0.003, 0, 90, 6)
    prof += [(0.0, d["cap_top"])]
    parts.append(lib.lathe("lid", prof, mats["white"]))

    # flip cover across the top, clear window on it, latch tab at the left, hinge at the right
    cl, cw, ch = d["cover_size"]
    top = d["cap_top"]
    parts.append(lib.rounded_box("cover", (cl, cw, ch), (-0.003, 0.0, top + ch / 2 - 0.0005), 0.0028, mats["white"]))
    wl_, ww, wh = d["window_size"]
    # a hairline above the cover: overlapping clear and opaque solids render black
    parts.append(lib.rounded_box("window", (wl_, ww, wh), (-0.004, 0.0, top + ch - 0.0005 + wh / 2 + 0.00005),
                                 0.0012, mats["window"]))
    lx, ly, lz = d["latch_size"]
    parts.append(lib.rounded_box("latch", (lx, ly, lz), (-(cr + lx / 2 + 0.0008), 0.0, top + ch - lz / 2 - 0.0005),
                                 0.0012, mats["white"]))
    parts.append(lib.cylinder("hinge", d["hinge_radius"], cw - 0.004, (cl / 2 - 0.006, 0.0, top + 0.002),
                              mats["white"], axis="Y"))

    # clear strap: a band around the bottle and a flat loop sticking out at the front, drooping a little
    z0, z1 = d["band_z"]
    bt, bf, rin = d["band_thickness"], 0.0006, R + 0.0002
    ring = [(rin, z0 + bf), (rin, z1 - bf), (rin + bt, z1 - bf), (rin + bt, z0 + bf), (rin, z0 + bf)]
    parts.append(lib.lathe("strap_band", ring, mats["strap"]))
    w, reach = d["loop_size"]
    zc, rout = (z0 + z1) / 2, rin + bt
    y_in = -(rout - 0.0005)        # the loop starts inside the band, clear of the bottle wall
    pts = [(w / 2 * math.cos(a), y_in - reach / 2 - reach / 2 * math.sin(a), zc)
           for a in (2 * math.pi * k / 64 for k in range(64))]
    loop = lib.ribbon("strap_loop", pts, (z1 - z0) * 0.85, bt, mats["strap"], closed=True)
    # a positive turn about +X lowers the part that sticks out towards -Y: the loop hangs down
    parts.append(lib.transform(loop, rotate_deg=(d["loop_droop_deg"], 0, 0), about=(0, y_in, zc)))

    # straw down to the bottom with its weight
    a = math.radians(d["straw_angle_deg"])
    sx, sy = d["straw_offset"] * math.sin(a), -d["straw_offset"] * math.cos(a)
    z_lo = base + 0.008
    parts.append(lib.cylinder("straw", d["straw_radius"], d["neck_top"] - z_lo, (sx, sy, (z_lo + d["neck_top"]) / 2),
                              mats["straw"]))
    parts.append(lib.sphere("straw_weight", 0.0055, (sx, sy, base + 0.0058), mats["straw"]))
    # the straw stands in the water: cut its shape (plus a hair) out of the water so the two solids do not overlap
    water = parts[1]
    lib.boolean(water, lib.cylinder("straw_cut", d["straw_radius"] + 0.0002, d["neck_top"] - z_lo + 0.002,
                                    (sx, sy, (z_lo + d["neck_top"]) / 2), None))
    lib.boolean(water, lib.sphere("weight_cut", 0.0057, (sx, sy, base + 0.0058), None))

    # the "SPORT" print, reading top to bottom just right of the front
    sport = lib.text_image("SPORT", lib.work_path("sport.png"))
    parts.append(lib.decal_on_cylinder("print", lib.image_material("print_white", sport, color=(0.85, 0.85, 0.85)),
                                       R, d["print_z"][0], d["print_z"][1], d["print_angle_deg"],
                                       d["print_height"], along="height"))
    return parts
