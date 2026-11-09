"""Render the master on all CPU cores: split the timeline into segments, render each in its own
process (frames are deterministic, so segments join seamlessly), concat losslessly, then mix/mux audio.

A watchdog restarts any segment that stops making progress (no log output and no output growth for --stall
seconds, default 300) up to 3 times; every start, stall, retry and finish is timestamped in out/render-log.md, so a
stuck render is visible from the log instead of waiting on it.

    python wbx/parallel.py --project projects/my-video                  # source resolution, 60 fps
    python wbx/parallel.py --project projects/my-video --jobs 6 --mb 6  # with motion blur
"""
import argparse
import math
import os
import subprocess
import sys
import time
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
    ap.add_argument("--stall", type=int, default=300, help="seconds without progress before a segment is restarted")
    ap.add_argument("--tries", type=int, default=3)
    a = ap.parse_args()

    from wbx.render import Project
    P = Project(a.project)
    end = P.duration
    seg = math.ceil(end / a.jobs)
    out_dir = P.dir / "out"
    out_dir.mkdir(exist_ok=True)
    log_md = out_dir / "render-log.md"

    def note(msg):
        line = f"- [{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
        print(line, flush=True)
        with open(log_md, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def launch(job):
        job["log"] = out_dir / f"_part_{job['s']:05d}.log"
        fh = open(job["log"], "a", encoding="utf-8")
        job["proc"] = subprocess.Popen([sys.executable, str(KIT / "wbx/render.py"), "--project", str(P.dir),
                                        "--start", str(job["s"]), "--end", str(job["e"]), "--fps", str(a.fps),
                                        "--res-scale", str(a.res_scale), "--mb", str(a.mb), "--no-audio",
                                        "--silent-out", str(job["part"])], stdout=fh, stderr=subprocess.STDOUT,
                                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        fh.close()
        job["try"] += 1
        job["sig"], job["seen"] = None, time.time()
        note(f"segment {job['s']}-{job['e']:.1f}s: start (try {job['try']})")

    jobs, parts = [], []
    for s in range(0, math.ceil(end), seg):
        e = min(s + seg, end)
        part = out_dir / f"_part_{s:05d}.mp4"
        parts.append(part)
        (out_dir / f"_part_{s:05d}.log").write_text("", "utf-8")
        jobs.append({"s": s, "e": e, "part": part, "try": 0, "t0": time.time()})
    note(f"render {P.dir.name}: {len(jobs)} segments, {a.fps} fps, res {a.res_scale}, mb {a.mb}")
    for job in jobs:
        launch(job)
    print(f"rendering {len(jobs)} segments in parallel (logs: {out_dir}/_part_*.log) ...", flush=True)
    failed = False
    while any(j["proc"].poll() is None for j in jobs):
        time.sleep(5)
        for job in jobs:
            p = job["proc"]
            if p.poll() is not None:
                continue
            sig = (job["log"].stat().st_size, job["part"].stat().st_size if job["part"].exists() else 0)
            if sig != job["sig"]:
                job["sig"], job["seen"] = sig, time.time()
            elif time.time() - job["seen"] > a.stall:
                p.kill()
                p.wait()
                note(f"segment {job['s']}-{job['e']:.1f}s: no progress for {a.stall}s, killed")
                if job["try"] < a.tries:
                    launch(job)
                else:
                    failed = True
    for job in jobs:
        rc = job["proc"].returncode
        if rc == 0 and job["part"].exists():
            note(f"segment {job['s']}-{job['e']:.1f}s: done ({(time.time() - job['t0']) / 60:.1f} min)")
        else:
            failed = True
            tail = job["log"].read_text("utf-8", errors="replace").strip().splitlines()[-1:] or [""]
            note(f"segment {job['s']}-{job['e']:.1f}s: FAILED (rc {rc}) {tail[0][:200]}")
    if failed:
        sys.exit(f"a segment failed — see {log_md} and the _part_*.log files")
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
    note(f"master done -> {out}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Chinese text on a Windows console or pipe
    main()
