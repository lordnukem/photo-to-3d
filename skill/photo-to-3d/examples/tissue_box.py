"""Tissue box with an oval opening and a label cut out of a photo - tests extrude, boolean, crop_image, decal_on_plane."""
import math

DIMS = {"size": (0.24, 0.12, 0.09), "opening": (0.13, 0.035)}   # given
ASSUMPTIONS = ["Opening cut straight through the top, 3 mm cardboard."]
VIEWS = {"front": (0, 10, 60), "three_quarter": (-35, 30, 45), "top": (0, 88, 50)}


def build(lib):
    d = DIMS
    sx, sy, sz = d["size"]
    card = lib.preset("plastic", "card", color=lib.color("#8c9eb3"), roughness=0.7)
    t = 0.003                       # cardboard
    box = lib.rounded_box("box", (sx, sy, sz), (0.0, 0.0, sz / 2), 0.004, card)
    lib.boolean(box, lib.rounded_box("hollow", (sx - 2 * t, sy - 2 * t, sz - 2 * t), (0.0, 0.0, sz / 2), 0.002, None))
    ox, oy = d["opening"]
    oval = [(ox / 2 * math.cos(2 * math.pi * k / 48), oy / 2 * math.sin(2 * math.pi * k / 48)) for k in range(48)]
    lib.boolean(box, lib.extrude("cutter", oval, sz - 2 * t - 0.002, sz + 0.002, None))   # through the top only
    # the "SPORT" lettering from the bottle photo, cut out and stuck on the front
    crop = lib.crop_image("photos/photo_01.jpg", (0.47, 0.57, 0.60, 0.92), lib.work_path("label.png"))
    label = lib.decal_on_plane("label", lib.image_material("label", crop), (0.0, -sy / 2, sz / 2), (0.05, 0.07))
    return [box, label]
