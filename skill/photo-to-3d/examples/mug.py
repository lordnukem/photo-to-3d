"""White ceramic mug with a C handle and COFFEE printed around it - from the notes only (no photo)."""
import math

DIMS = {
    "height": 0.095,         # given
    "radius": 0.040,         # given: 8 cm across
    "wall": 0.004,           # est
    "base": 0.007,           # est
    "handle_radius": 0.006,  # est: thickness of the handle
    "handle_reach": 0.032,   # est: how far the handle sticks out
}
ASSUMPTIONS = ["Wall 4 mm, base 7 mm.", "Handle on the right side, seen from the front."]
VIEWS = {"front": (0, 10, 70), "three_quarter": (-35, 25, 50), "right": (90, 10, 70), "top": (0, 88, 60)}


def build(lib):
    d = DIMS
    ceramic = lib.preset("ceramic", "white_ceramic", color=(0.92, 0.92, 0.90))
    R, H, t, b = d["radius"], d["height"], d["wall"], d["base"]
    f = 0.004
    prof = [(0.0, 0.0), (R - f, 0.0)] + lib.arc(R - f, f, f, -90, 0) + [(R, H - t / 2)]
    prof += lib.arc(R - t / 2, H - t / 2, t / 2, 0, 180, 6)       # rounded rim, its top exactly at H
    prof += [(R - t, b + 0.004)] + lib.arc(R - t - 0.004, b + 0.004, 0.004, 0, -90) + [(0.0, b)]
    body = lib.lathe("body", prof, ceramic)
    # C handle on the right (+X), ends sunk a little into the wall
    reach, z_lo, z_hi = d["handle_reach"], 0.022, 0.077
    pts = [(R - 0.003, 0.0, z_hi), (R + reach * 0.7, 0.0, z_hi + 0.004), (R + reach, 0.0, (z_lo + z_hi) / 2 + 0.006),
           (R + reach * 0.8, 0.0, z_lo + 0.004), (R - 0.003, 0.0, z_lo)]
    handle = lib.tube("handle", pts, d["handle_radius"], ceramic)
    word = lib.text_image("COFFEE", lib.work_path("coffee.png"), color=(60, 60, 60))
    ink = lib.image_material("ink", word)
    text = lib.decal_on_cylinder("print", ink, R, 0.040, 0.062, 0.0, 0.10, along="around")
    return [body, handle, text]
