"""Check a fresh install: ffmpeg, Python packages, and one still per template drawn from its starter project with
a made-up four-line transcript (no clip needed).

    python tools/selftest.py            # stills land in a temp folder; prints OK or what is missing
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
STARTERS = {1: "project", 2: "project-popcard", 3: "project-softglass"}
LINES = [("这是一段测试视频，", "This is a test clip,"), ("用来检查安装。", "to check the install."),
         ("第一点很简单，", "The first point is simple,"), ("谢谢观看。", "thanks for watching.")]


def fake_project(proj, starter):
    shutil.copytree(KIT / "templates" / starter, proj)
    (proj / "data").mkdir()
    src = dict(file="input/source.mp4", width=1080, height=1440, fps=30.0, duration=12.0, aspect="1080:1440",
               crop=[294, 230, 492, 656], crop_note="selftest")
    caps = []
    for i, (zh, en) in enumerate(LINES):
        t0, chars = i * 3.0, list(zh)
        step = 2.4 / len(chars)
        units = [dict(text=ch, start=round(t0 + j * step, 3), end=round(t0 + (j + 1) * step, 3)) for j, ch in enumerate(chars)]
        caps.append(dict(id=f"c{i:03d}", t0=t0, t1=t0 + 2.4, zh=zh, en=en,
                         highlight=dict(source="selftest", language="zh", units=units)))
    (proj / "data/source.json").write_text(json.dumps(src, indent=1), "utf-8")
    (proj / "data/captions.json").write_text(json.dumps(caps, ensure_ascii=False, indent=1), "utf-8")


def main():
    bad = []
    for exe in ("ffmpeg", "ffprobe"):
        if not shutil.which(exe):
            bad.append(f"{exe} not on PATH (Windows: winget install Gyan.FFmpeg, macOS: brew install ffmpeg)")
    for mod in ("skia", "numpy", "cv2", "faster_whisper"):
        try:
            __import__(mod)
        except Exception as e:
            bad.append(f"python package {mod}: {e}")
    if not shutil.which("ffmpeg"):
        sys.exit("\n".join(bad))
    tmp = Path(tempfile.mkdtemp(prefix="aicut-selftest-"))
    for n, starter in STARTERS.items():
        proj = tmp / starter
        fake_project(proj, starter)
        r = subprocess.run([sys.executable, str(KIT / "wbx/render.py"), "--project", str(proj), "--res-scale", "0.25",
                            "--stills", "1,7.5"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        pngs = sorted((proj / "out/stills").glob("*.png"))
        if r.returncode or len(pngs) < 2:
            bad.append(f"Template {n} still failed:\n{r.stdout[-800:]}{r.stderr[-1500:]}")
        else:
            print(f"Template {n}: {pngs[-1]}")
    if bad:
        sys.exit("\n".join(["PROBLEMS:"] + bad))
    print("OK: aicut is ready")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Chinese text on a Windows console or pipe
    main()
