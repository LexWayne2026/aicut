"""Scaffold a project from a talking-head clip.

    python tools/new_project.py path/to/clip.mp4 projects/my-video [--link] [--no-asr] [--model large-v3] [--lang zh] [--template 1|2|3]

Creates projects/my-video/{input,data,out}, copies (or symlinks) the clip to input/source.<ext>, probes it
(size/fps/duration/face crop/silences -> data/source.json), transcribes it (-> data/captions.json,
data/transcript.txt) and drops in starter timeline.py + scenes.py for the template (1 whiteboard, 2 Pop Card, 3 Soft Glass).
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip")
    ap.add_argument("project")
    ap.add_argument("--link", action="store_true", help="symlink the clip instead of copying it")
    ap.add_argument("--no-asr", action="store_true")
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--lang", default=None)
    ap.add_argument("--template", type=int, choices=[1, 2, 3], default=1, help="1 whiteboard, 2 Pop Card, 3 Soft Glass")
    a = ap.parse_args()
    clip = Path(a.clip).resolve()
    proj = Path(a.project).resolve()
    for d in ("input", "data", "out"):
        (proj / d).mkdir(parents=True, exist_ok=True)
    dst = proj / "input" / f"source{clip.suffix.lower()}"
    if not dst.exists():
        if a.link:
            try:
                dst.symlink_to(clip)
            except OSError:                 # Windows without Developer Mode: hard link, else copy
                try:
                    dst.hardlink_to(clip)
                except OSError:
                    shutil.copy2(clip, dst)
        else:
            shutil.copy2(clip, dst)
    for f in ("timeline.py", "scenes.py"):
        if not (proj / f).exists():
            shutil.copy2(KIT / "templates" / {1: "project", 2: "project-popcard", 3: "project-softglass"}[a.template] / f, proj / f)
    subprocess.run([sys.executable, str(KIT / "tools/probe.py"), str(proj)], check=True)
    if not a.no_asr:
        cmd = [sys.executable, str(KIT / "tools/transcribe.py"), str(proj), "--model", a.model]
        if a.lang:
            cmd += ["--lang", a.lang]
        subprocess.run(cmd, check=True)
    print(f"\nproject ready: {proj}\nnext: review data/transcript.txt, then write timeline.py + scenes.py")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Chinese text on a Windows console or pipe
    main()
