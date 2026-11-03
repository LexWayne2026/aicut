"""Rebuild the README gallery in docs/ from the demo projects: one GIF and one strip of four stills per template.
Run demo/make_demo.py first; this renders the previews it needs.

    python demo/make_gallery.py
"""
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
DOCS = KIT / "docs"
GIF_SPAN = (4.8, 18.8)          # hook payoff through the dose chart
STILLS = {"whiteboard": (1.2, 6.4, 18.2, 30.8), "popcard": (5.9, 9.6, 18.6, 30.0), "softglass": (5.9, 9.8, 18.4, 30.0)}


def run(*cmd):
    subprocess.run([str(x) for x in cmd], check=True)


def main():
    DOCS.mkdir(exist_ok=True)
    for name, times in STILLS.items():
        proj = KIT / "demo" / name
        prev = proj / "out" / f"{name}-gallery.mp4"
        if not prev.exists():
            run(sys.executable, KIT / "wbx/render.py", "--project", proj, "--preview", "--out", prev)
        a, b = GIF_SPAN
        flt = "fps=12,scale=360:-1:flags=lanczos,split[x][y];[x]palettegen=max_colors=256:stats_mode=full[p];[y][p]paletteuse=dither=sierra2_4a"
        run("ffmpeg", "-v", "error", "-y", "-ss", a, "-t", b - a, "-i", prev, "-filter_complex", flt, DOCS / f"{name}.gif")
        run(sys.executable, KIT / "wbx/render.py", "--project", proj, "--res-scale", "0.5", "--stills", ",".join(map(str, times)))
        shots = [proj / "out/stills" / f"t{t:07.2f}.png" for t in times]
        ins = [x for s in shots for x in ("-i", s)]
        stack = "".join(f"[{i}:v]scale=360:-1[s{i}];" for i in range(len(shots))) + "".join(f"[s{i}]" for i in range(len(shots)))
        run("ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", stack + f"hstack=inputs={len(shots)}", "-q:v", "3",
            DOCS / f"{name}-stills.jpg")
        print("gallery:", name)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Chinese text on a Windows console or pipe
    main()
