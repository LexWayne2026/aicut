"""Contact sheets for review (the director looks at sheets, not at single big frames).

    python tools/sheet.py projects/my-video                      # from out/stills/*.png
    python tools/sheet.py projects/my-video --video out/x.mp4 --every 6
"""
import argparse
import subprocess
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--video", default=None)
    ap.add_argument("--every", type=float, default=6.0)
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--thumb", type=int, default=320, help="thumbnail width")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    proj = Path(a.project).resolve()
    out = Path(a.out) if a.out else proj / "out" / ("sheet-video.jpg" if a.video else "sheet-stills.jpg")
    if a.video:
        v = proj / a.video if not Path(a.video).is_absolute() else Path(a.video)
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                    str(v)], capture_output=True, text=True).stdout)
        n = int(dur // a.every) + 1
        rows = (n + a.cols - 1) // a.cols
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(v), "-vf",
                        f"fps=1/{a.every},scale={a.thumb}:-2,tile={a.cols}x{rows}", "-frames:v", "1", str(out)],
                       check=True)
    else:
        files = sorted((proj / "out/stills").glob("t*.png"))
        rows = (len(files) + a.cols - 1) // a.cols
        lst = proj / "out/stills/_list.txt"            # concat list, not -pattern_type glob (absent on Windows)
        lst.write_text("".join(f"file '{f.as_posix()}'\n" for f in files), "utf-8")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                        "-vf", f"scale={a.thumb}:-2,tile={a.cols}x{rows}", "-frames:v", "1", str(out)], check=True)
        lst.unlink()
    print(out)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Chinese text on a Windows console or pipe
    main()
