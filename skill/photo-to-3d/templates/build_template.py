"""OBJECT NAME - built from photos/ and notes.md.

Metres; Z up; the object stands on z = 0 centred on the Z axis; its front faces -Y.
Run: model3d build THIS_FOLDER            (quick preview renders + comparison sheet)
     model3d build THIS_FOLDER --final    (final renders, about 10 min per view on a 2-core CPU)
"""

# Every size in one place. Mark where it came from: "given" (the user said so) or "est" (read off the photos).
DIMS = {
    "height": 0.100,          # est
    "radius": 0.040,          # est
}

# What the model assumes that the photos and notes do not settle; shown to the user with the result.
ASSUMPTIONS = [
    "No size given: height estimated at 10 cm.",
]

# Views to render: name -> (azimuth degrees right of the front, elevation degrees, lens mm).
# Add one view per photo that looks from the same direction as that photo, so the sheet compares like with like.
VIEWS = {
    "front": (0, 8, 70),
    "three_quarter": (-35, 25, 50),
    "back": (180, 15, 60),
    "top": (0, 88, 60),
}


def build(lib):
    d = DIMS
    body_mat = lib.preset("plastic", "body", color=(0.8, 0.8, 0.8))
    # profile from the bottom centre, up the outside, across the top, back to the axis: a closed solid
    r, h, f = d["radius"], d["height"], 0.003
    profile = [(0.0, 0.0), (r - f, 0.0)] + lib.arc(r - f, f, f, -90, 0) + [(r, h - f)] + lib.arc(r - f, h - f, f, 0, 90)
    profile += [(0.0, h)]
    body = lib.lathe("body", profile, body_mat)
    return [body]
