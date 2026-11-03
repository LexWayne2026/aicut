"""Render the master on all CPU cores: split the timeline into segments, render each in its own
process (frames are deterministic, so segments join seamlessly), concat losslessly, then mix/mux audio.

    python wbx/parallel.py --project projects/my-video                  # source resolution, 60 fps
    python wbx/parallel.py --project projects/my-video --jobs 6 --mb 6  # with motion blur
"""
import argparse
import math
import os
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--res-scale", type=float, default=1.0)
    ap.add_argument("--mb", type=int, default=1)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    from wbx.render import Project
    P = Project(a.project)
    end = P.duration
    seg = math.ceil(end / a.jobs)
    out_dir = P.dir / "out"
    out_dir.mkdir(exist_ok=True)
    procs, parts = [], []
    for s in range(0, math.ceil(end), seg):
        e = min(s + seg, end)
        part = out_dir / f"_part_{s:05d}.mp4"
        parts.append(part)
        log = open(out_dir / f"_part_{s:05d}.log", "w", encoding="utf-8")
        procs.append(subprocess.Popen([sys.executable, str(KIT / "wbx/render.py"), "--project", str(P.dir),
                                       "--start", str(s), "--end", str(e), "--fps", str(a.fps),
                                       "--res-scale", str(a.res_scale), "--mb", str(a.mb), "--no-audio",
                                       "--silent-out", str(part)], stdout=log, stderr=subprocess.STDOUT,
                                      env={**os.environ, "PYTHONIOENCODING": "utf-8"}))
    print(f"rendering {len(procs)} segments in parallel (logs: {out_dir}/_part_*.log) ...", flush=True)
    for p in procs:
        if p.wait() != 0:
            sys.exit("a segment failed — see the _part_*.log files")
    lst = out_dir / "_parts.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in parts), "utf-8")
    silent = out_dir / "_video_master_joined.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                    str(silent)], check=True)
    from wbx.audio import build_mix
    mix = build_mix(P, 0, end)
    out = a.out or str(out_dir / f"{P.dir.name}-master.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(silent), "-i", str(mix), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-shortest", "-movflags", "+faststart", out],
                   check=True)
    print(f"done -> {out}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Chinese text on a Windows console or pipe
    main()
