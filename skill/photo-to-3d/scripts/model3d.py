#!/usr/bin/env python3
"""model3d: model an object in Blender from photos and notes.

  model3d new NAME [--photo FILE ...] [--notes TEXT]   make models/NAME/ with photos/, notes.md and build.py
  model3d build MODEL_DIR [--final] [--views a,b] [--clay] [--no-render]
                                                      run build.py in Blender: export GLB/OBJ/.blend, render,
                                                      and put the renders next to the photos
  model3d sheet MODEL_DIR [--final]                   redo only the comparison sheet
  model3d check                                       check Blender, its Python modules and the font

Model folders live in $PHOTO3D_HOME/models (default ~/photo-to-3d/models).
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser(os.environ.get("PHOTO3D_HOME", "~/photo-to-3d"))
# DejaVu Sans: $PHOTO3D_FONT, else the usual places on Debian/Ubuntu, Fedora, Arch and macOS
FONT_PLACES = [os.environ.get("PHOTO3D_FONT", ""), "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
               "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf", "/usr/share/fonts/TTF/DejaVuSans.ttf",
               "/usr/share/fonts/dejavu/DejaVuSans.ttf", "/Library/Fonts/DejaVuSans.ttf",
               os.path.expanduser("~/Library/Fonts/DejaVuSans.ttf")]
FONT = next((f for f in FONT_PLACES if f and os.path.exists(f)), FONT_PLACES[1])
MODELS = os.path.join(HOME, "models")
PHOTO_EXT = (".jpg", ".jpeg", ".png", ".webp")


def blender_cmd(*extra):
    return ["nice", "-n", "10", "blender", "-b", "--factory-startup", "--python-exit-code", "1", *extra]


def cmd_new(a):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", a.name):
        print(f"name {a.name!r}: use letters, digits, '-', '_' or '.', starting with a letter or digit", file=sys.stderr)
        return 2
    folder = os.path.join(MODELS, a.name)
    if os.path.exists(folder):
        print(f"{folder} already exists", file=sys.stderr)
        return 2
    bad = [f"{p}: not found" for p in a.photo or [] if not os.path.isfile(p)]
    bad += [f"{p}: only {', '.join(PHOTO_EXT)} can be read (convert HEIC to JPG first)" for p in a.photo or []
            if os.path.isfile(p) and os.path.splitext(p)[1].lower() not in PHOTO_EXT]
    if bad:                                          # check everything before creating anything
        print("\n".join(bad), file=sys.stderr)
        return 2
    os.makedirs(os.path.join(folder, "photos"))
    for i, src in enumerate(a.photo or [], 1):
        shutil.copyfile(src, os.path.join(folder, "photos", f"photo_{i:02d}{os.path.splitext(src)[1].lower()}"))
    with open(os.path.join(HERE, "..", "templates", "notes_template.md")) as f:
        notes = f.read().replace("{NAME}", a.name).replace("{NOTES}", a.notes or "(none given)")
    with open(os.path.join(folder, "notes.md"), "w") as f:
        f.write(notes)
    shutil.copyfile(os.path.join(HERE, "..", "templates", "build_template.py"), os.path.join(folder, "build.py"))
    print(folder)
    return 0


def cmd_build(a):
    folder = os.path.abspath(a.model_dir)
    build = os.path.join(folder, "build.py")
    if not os.path.exists(build):
        print(f"no build.py in {folder}", file=sys.stderr)
        return 2
    out = os.path.join(folder, "out")
    os.makedirs(out, exist_ok=True)
    quality = "final" if a.final else "preview"
    cmd = blender_cmd("-P", os.path.join(HERE, "blender_runner.py"), "--", "--model", build, "--out", out,
                      "--quality", quality, "--name", os.path.basename(folder.rstrip("/")))
    if a.views:
        cmd += ["--views", a.views]
    if a.clay:
        cmd.append("--clay")
    if a.no_render:
        cmd.append("--no-render")
    log_path = os.path.join(out, f"build-{quality}.log")
    t0 = time.time()
    with open(log_path, "w") as log:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            log.write(line)
            if line.startswith(("rendered ", "WARNING", "size (x, y, z)", "BUILD OK", "print part ")):
                print(line.rstrip(), flush=True)
        proc.wait()
    with open(log_path) as f:
        text = f.read()
    if proc.returncode != 0 or "BUILD OK" not in text:
        tail = text.strip().splitlines()[-25:]
        print(f"FAILED (exit {proc.returncode}) after {time.time() - t0:.0f} s; log: {log_path}", file=sys.stderr)
        print("\n".join(tail), file=sys.stderr)
        return 1
    if not a.no_render:
        sheet(folder, quality)
    print(f"done in {time.time() - t0:.0f} s; outputs in {out}")
    return 0


def sheet(folder, quality):
    """Photos (top row) and renders (bottom row) on one image: out/comparison-<quality>.png."""
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    out = os.path.join(folder, "out")
    if not os.path.exists(os.path.join(out, "model_info.json")):
        raise SystemExit(f"no finished build in {folder}: run model3d build first (or read out/build-*.log)")
    with open(os.path.join(out, "model_info.json")) as f:
        info = json.load(f)
    photos = sorted(p for p in glob.glob(os.path.join(folder, "photos", "*")) if p.lower().endswith(PHOTO_EXT))
    if info.get("quality") != quality:
        raise SystemExit(f"the last build made {info.get('quality')} renders, not {quality}: run model3d build first")
    renders = [r for r in info["outputs"]["renders"].values() if os.path.exists(r)]   # what the last build rendered
    if not renders:
        raise SystemExit("the last build rendered nothing (--no-render?): run model3d build without it")
    font = ImageFont.truetype(FONT, 18)
    H = 420

    def row(paths, label):
        tiles = []
        for p in paths:
            with Image.open(p) as im:
                im = ImageOps.exif_transpose(im).convert("RGB")
                tiles.append((f"{label}{os.path.splitext(os.path.basename(p))[0]}",
                              im.resize((max(1, round(im.width * H / im.height)), H))))
        return tiles

    rows = [r for r in (row(photos, "photo: "), row(renders, "")) if r]
    width = max(sum(im.width + 10 for _, im in r) + 10 for r in rows)
    img = Image.new("RGB", (width, len(rows) * (H + 40) + 10), (30, 30, 30))
    draw = ImageDraw.Draw(img)
    y = 10
    for r in rows:
        x = 10
        for name, im in r:
            draw.text((x, y), name, fill=(230, 230, 230), font=font)
            img.paste(im, (x, y + 26))
            x += im.width + 10
        y += H + 40
    path = os.path.join(out, f"comparison-{quality}.png")
    img.save(path)
    print(f"comparison sheet: {path}")
    return path


def cmd_sheet(a):
    sheet(os.path.abspath(a.model_dir), "final" if a.final else "preview")
    return 0


def cmd_check(a):
    ok = True
    blender = shutil.which("blender")
    print(f"[{'ok' if blender else 'MISSING'}] blender {blender or ''}")
    if blender:
        probe = ("import sys; sys.path.insert(0, %r); import p3d_blender, numpy, PIL, bpy; "
                 "print('PROBE', bpy.app.version_string, 'numpy', numpy.__version__, 'Pillow', PIL.__version__)" % HERE)
        r = subprocess.run(blender_cmd("--python-expr", probe), capture_output=True, text=True, timeout=120)
        line = next((ln for ln in r.stdout.splitlines() if ln.startswith("PROBE")), None)
        print(f"[{'ok' if line else 'FAIL'}] Blender Python: {line[6:] if line else r.stdout[-400:] + r.stderr[-400:]}")
        ok &= bool(line)
    font = os.path.exists(FONT)
    print(f"[{'ok' if font else 'MISSING'}] DejaVu Sans font {FONT if font else '(set PHOTO3D_FONT)'} (sheets and text)")
    print(f"[ok] model folders: {MODELS}")
    return 0 if ok and blender and font else 1


def main():
    p = argparse.ArgumentParser(prog="model3d", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("name")
    n.add_argument("--photo", action="append")
    n.add_argument("--notes")
    n.set_defaults(fn=cmd_new)
    b = sub.add_parser("build")
    b.add_argument("model_dir")
    b.add_argument("--final", action="store_true", help="600x800, 160 samples (about 10 min per view on a 2-core CPU)")
    b.add_argument("--views")
    b.add_argument("--clay", action="store_true")
    b.add_argument("--no-render", action="store_true")
    b.set_defaults(fn=cmd_build)
    s = sub.add_parser("sheet")
    s.add_argument("model_dir")
    s.add_argument("--final", action="store_true")
    s.set_defaults(fn=cmd_sheet)
    c = sub.add_parser("check")
    c.set_defaults(fn=cmd_check)
    a = p.parse_args()
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()
