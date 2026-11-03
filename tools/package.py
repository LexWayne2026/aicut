"""Build a self-contained RENDER KIT zip for rendering on another (faster) machine.

    python tools/package.py projects/my-video [--out path.zip] [--no-video]

The kit contains: wbx/ engine, fonts/, music/, requirements.txt, RENDER.md and run scripts, plus the
project (timeline.py, scenes.py, data/, input/ with the source clip; out/ is left empty).
On the render machine:  pip install -r requirements.txt  &&  python wbx/parallel.py --project projects/<name>
"""
import argparse
import re
import zipfile
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
SKIP = {"__pycache__", ".DS_Store", "out"}


def add_tree(z, root, arc_root, skip_dirs=SKIP):
    for p in sorted(root.rglob("*")):
        if any(part in skip_dirs for part in p.relative_to(root).parts):
            continue
        if p.is_file() or (p.is_symlink() and p.resolve().is_file()):
            z.write(p.resolve() if p.is_symlink() else p, f"{arc_root}/{p.relative_to(root)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-video", action="store_true", help="leave the source clip out (copy it manually)")
    a = ap.parse_args()
    proj = Path(a.project).resolve()
    name = proj.name
    out = Path(a.out) if a.out else proj.parent / f"{name}-render-kit.zip"
    root = f"{name}-render-kit"
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as z:
        for d in ("wbx", "music"):
            add_tree(z, KIT / d, f"{root}/{d}")
        m = re.search(r"^TEMPLATE\s*=\s*(\d)", (proj / "timeline.py").read_text("utf-8"), re.M)
        keep = {1: ("LXGW",), 2: ("ResourceHan", "Outfit-ExtraBold", "Outfit-Medium"),
                3: ("NotoSansSC", "Outfit-SemiBold", "Outfit-Medium")}[int(m.group(1)) if m else 1]
        for p in sorted((KIT / "fonts").iterdir()):       # only this template's fonts; licences always
            if p.suffix != ".ttf" or p.name.startswith(keep):
                z.write(p, f"{root}/fonts/{p.name}")
        for f in ("requirements.txt", "RENDER.md", "render.sh", "render.bat"):
            z.write(KIT / "templates/kit" / f, f"{root}/{f}")
        skip = SKIP | ({"input"} if a.no_video else set())
        add_tree(z, proj, f"{root}/projects/{name}", skip)
        z.writestr(f"{root}/projects/{name}/out/.keep", "")
    print(f"{out}  ({out.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Chinese text on a Windows console or pipe
    main()
