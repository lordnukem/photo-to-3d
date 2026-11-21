"""Runs inside Blender: build a model from its build.py, check it, export it and render it.

  blender -b --factory-startup --python-exit-code 1 -P blender_runner.py -- --model DIR/build.py --out DIR/out
          [--quality preview|final] [--views a,b] [--clay] [--no-render] [--name model]

Called by `model3d build`; prints "BUILD OK" at the end. Anything else (a traceback) is a failure.
"""
import argparse
import importlib.util
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import p3d_blender as lib  # noqa: E402


def args():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--quality", default="preview", choices=list(lib.QUALITY))
    p.add_argument("--views", default="", help="comma-separated view names (default: all of the model's VIEWS)")
    p.add_argument("--clay", action="store_true", help="also render the views in plain grey to judge the shape")
    p.add_argument("--no-render", action="store_true")
    p.add_argument("--name", default="model")
    return p.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])


def main():
    a = args()
    model_path, out = os.path.abspath(a.model), os.path.abspath(a.out)
    os.makedirs(os.path.join(out, "work"), exist_ok=True)
    stale = os.path.join(out, "model_info.json")     # describes the last good build; a failed one must not keep it
    if os.path.exists(stale):
        os.remove(stale)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    os.chdir(os.path.dirname(model_path))           # paths in build.py are relative to the model folder
    spec = importlib.util.spec_from_file_location("model_build", model_path)
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)
    lib.WORK_DIR = os.path.join(out, "work")        # generated images (text, crops) go here

    t0 = time.time()
    parts = model.build(lib)
    if not parts or any(getattr(p, "type", None) != "MESH" for p in parts):
        raise SystemExit("build(lib) must return a list of mesh objects (the parts to export)")
    stats = lib.measure(parts)
    empty = [n for n, p in stats["parts"].items() if p["faces"] == 0]
    if empty:
        raise SystemExit(f"part(s) without faces: {empty}")
    glb, obj = lib.export(out, parts, a.name)
    print_report = {}
    groups = getattr(model, "PRINT_PARTS", None)       # {part name: [object names]} for 3D printing
    if groups:
        by_name = {p.name: p for p in parts}
        missing = [n for names in groups.values() for n in names if n not in by_name]
        if missing:
            raise SystemExit(f"PRINT_PARTS names objects that build() did not return: {missing}")
        print_report = lib.export_print_parts(os.path.join(out, "print"),
                                              {g: [by_name[n] for n in names] for g, names in groups.items()})
        for g, r in print_report.items():
            flag = "" if r["open_edges"] == 0 and r["shells"] == 1 else "   <- not a single closed solid"
            print(f"print part {g}: {r['size_mm']} mm, {r['volume_cm3']} cm3, {r['faces']} faces, "
                  f"open edges {r['open_edges']}, shells {r['shells']}{flag}", flush=True)
            if flag:
                stats["problems"].append(f"print part {g} is not a single closed solid "
                                         f"({r['open_edges']} open edges, {r['shells']} shells)")
    build_seconds = round(time.time() - t0, 1)

    views = dict(getattr(model, "VIEWS", None) or lib.DEFAULT_VIEWS)
    if a.views:
        unknown = [v for v in a.views.split(",") if v not in views]
        if unknown:
            raise SystemExit(f"unknown view(s) {unknown}; the model has {list(views)}")
        views = {v: views[v] for v in a.views.split(",")}
    lib.stage(stats["bbox_min"], stats["bbox_max"], a.quality)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, f"{a.name}.blend"))
    renders, times = {}, {}
    if not a.no_render:
        rdir = os.path.join(out, "renders", a.quality)
        t1 = time.time()
        renders = lib.render_views(rdir, views, stats["bbox_min"], stats["bbox_max"])
        times["renders"] = round(time.time() - t1, 1)
        if a.clay:
            t1 = time.time()
            renders.update({k + "_clay": v for k, v in
                            lib.render_views(rdir, views, stats["bbox_min"], stats["bbox_max"], clay=True).items()})
            times["clay_renders"] = round(time.time() - t1, 1)
    info = {"model": model_path, "quality": a.quality, "dims_m": getattr(model, "DIMS", {}),
            "assumptions": getattr(model, "ASSUMPTIONS", []), "views": views, "size_cm": stats["size_cm"],
            "parts": stats["parts"], "problems": stats["problems"], "build_seconds": build_seconds, "print_parts": print_report,
            "render_seconds": times, "outputs": {"glb": glb, "obj": obj, "blend": os.path.join(out, f"{a.name}.blend"),
                                                 "renders": renders}}
    with open(os.path.join(out, "model_info.json"), "w") as f:
        json.dump(info, f, indent=1)
    for problem in stats["problems"]:
        print(f"WARNING: {problem}", flush=True)
    print(f"size (x, y, z) cm: {stats['size_cm']}   parts: {len(parts)}", flush=True)
    print("BUILD OK", flush=True)


main()
