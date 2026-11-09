"""Check caption timing against the clip's own waveform (independent of Whisper), and optionally fix it.

    python tools/check_sync.py projects/my-video              # report only
    python tools/check_sync.py projects/my-video --fix        # snap line edges to the waveform, then report again

Whisper is reliably off after a pause: in Chinese it tends to start a line 5-10 frames EARLY, and an early caption
(text before sound) is the worst kind of drift. This tool measures every caption line's start and end against the
real audio and, with --fix, moves them onto the waveform edge.

How the check works (adapted from wave_onset_check.py in github.com/paxon-yang/talking-video-skills,
MIT licence, Copyright (c) 2026; notice in README.md):
- RMS loudness per video frame (--fps, default 30) in dB; threshold = max(p10 + 15 dB, p90 - 30 dB).
- Onset = first frame within +-WIN frames of the caption start that has >= MIN_SIL quiet frames before it and
  RUN loud frames from it on. Offset = the loud frame closest to the caption end with >= MIN_SIL quiet frames after.
- Lines that start or end inside continuous speech have no waveform edge to compare with: listed as n/a.
- Drift = caption - waveform, in frames (+ = caption late). PASS when every start is within +-3 frames and every
  end within +-6 frames. Exit code 0 PASS, 1 FAIL, 2 not measurable (fewer than a quarter of the lines start
  after a silence, e.g. a silent or music-covered clip).

--fix changes data/captions.json (backup: data/captions.before-sync.json): a line whose start or end drifts more
than 1 frame gets its t0/t1 AND its first/last unit moved onto the waveform edge, so at() cues move with it.
Only edges after/before real silence are touched; the inside of a line is left alone. Run it after the transcript
has been corrected and before storyboarding (cues are read from these times).
"""
import argparse
import json
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

import numpy as np


def loudness(src, fps):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-map", "0:a:0", "-ac", "1", "-ar", "48000",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32)
    hop = int(round(48000 / fps))
    n = len(x) // hop
    db = 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
    thr = max(np.percentile(db, 10) + 15, np.percentile(db, 90) - 30)
    return db > thr, float(thr)


def measure(caps, loud, fps, win, min_sil, run):
    n = len(loud)
    rows = []
    for c in caps:
        f0, f1 = c["t0"] * fps, c["t1"] * fps
        units = c.get("highlight", {}).get("units") or [dict(start=c["t0"], end=c["t1"])]
        # an edge belongs to this line only if it falls before its first unit ends / after its last unit starts;
        # otherwise the line starts or ends inside running speech and the nearest pause is someone else's edge
        lim0, lim1 = units[0]["end"] * fps, units[-1]["start"] * fps
        on = off = None
        for k in range(max(min_sil, int(f0) - win), min(n - run, int(f0) + win + 1)):
            if loud[k:k + run].all() and not loud[k - min_sil:k].any():
                on = k if k < lim0 else None
                break
        cands = [k for k in range(max(0, int(f1) - win), min(n - min_sil, int(f1) + win + 1))
                 if loud[k] and not loud[k + 1:k + 1 + min_sil].any() and k + 1 > lim1]
        if cands:
            off = min(cands, key=lambda k: abs(k - f1))
        rows.append(dict(id=c["id"], text=c["zh"], t0=c["t0"], t1=c["t1"], on=on, off=off,
                         d_start=None if on is None else round(f0 - on, 1),
                         d_end=None if off is None else round(f1 - (off + 1), 1)))
    return rows


def stat(v):
    if not v:
        return "n/a"
    a = sorted(abs(t) for t in v)
    p95 = a[min(len(a) - 1, int(round(.95 * (len(a) - 1))))]
    return (f"n={len(v)}  mean {statistics.mean(v):+.1f} f  mean abs {statistics.mean(a):.1f} f  "
            f"max abs {max(a):.0f} f  P95 {p95:.0f} f")


def report(rows, fps, thr, st_tol, en_tol):
    st = [r["d_start"] for r in rows if r["d_start"] is not None]
    en = [r["d_end"] for r in rows if r["d_end"] is not None]
    bad = [r for r in rows if (r["d_start"] is not None and abs(r["d_start"]) > st_tol)
           or (r["d_end"] is not None and abs(r["d_end"]) > en_tol)]
    early = sum(1 for x in st if x < -1)
    if len(st) < max(1, len(rows) // 4):      # silent or music-covered audio: nothing to measure against
        return None, (f"caption sync vs waveform  ({len(rows)} lines): NOT MEASURABLE — only {len(st)} line starts "
                      f"follow a real silence (threshold {thr:.1f} dB). Check by ear instead.")
    ok = not bad
    L = [f"caption sync vs waveform  ({len(rows)} lines, {fps:g} fps, threshold {thr:.1f} dB)",
         f"  start: {stat(st)}   (caption early by >1 f: {early})",
         f"  end  : {stat(en)}",
         f"  n/a (no silence at the edge): {sum(r['d_start'] is None for r in rows)} starts, "
         f"{sum(r['d_end'] is None for r in rows)} ends",
         f"  {'PASS' if ok else 'FAIL'}: start within +-{st_tol:g} f, end within +-{en_tol:g} f"
         + ("" if ok else f"  ({len(bad)} lines out)")]
    for r in sorted(bad, key=lambda r: -max(abs(r['d_start'] or 0), abs(r['d_end'] or 0)))[:12]:
        ds = "" if r["d_start"] is None else f"{r['d_start']:+.0f}"
        de = "" if r["d_end"] is None else f"{r['d_end']:+.0f}"
        L.append(f"    {r['id']}  {r['t0']:7.2f}-{r['t1']:7.2f}s  start {ds:>4} f  end {de:>4} f  {r['text']}")
    return ok, "\n".join(L)


def fix(caps, rows, fps):
    moved = 0
    for c, r in zip(caps, rows):
        units = c.get("highlight", {}).get("units") or []
        if r["d_start"] is not None and abs(r["d_start"]) > 1:
            t = round(r["on"] / fps, 3)
            if units and t < units[0]["end"]:
                units[0]["start"] = t
                c["t0"] = t
                moved += 1
        if r["d_end"] is not None and abs(r["d_end"]) > 1:
            t = round((r["off"] + 1) / fps, 3)
            if units and t > units[-1]["start"]:
                units[-1]["end"] = t
                c["t1"] = t
                moved += 1
    # keep lines in order and non-overlapping
    for a, b in zip(caps, caps[1:]):
        if a["t1"] > b["t0"]:
            a["t1"] = b["t0"]
            if a.get("highlight", {}).get("units"):
                a["highlight"]["units"][-1]["end"] = min(a["highlight"]["units"][-1]["end"], b["t0"])
    return moved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--win", type=int, default=15, help="search window around each edge, frames")
    ap.add_argument("--min-sil", type=int, default=4, help="quiet frames required before an onset / after an offset")
    ap.add_argument("--run", type=int, default=3, help="loud frames required after an onset")
    ap.add_argument("--start-tol", type=float, default=3)
    ap.add_argument("--end-tol", type=float, default=6)
    ap.add_argument("--fix", action="store_true", help="snap line edges to the waveform (backs up captions.json)")
    ap.add_argument("--json", help="write the per-line table here")
    a = ap.parse_args()

    proj = Path(a.project).resolve()
    src_meta = json.loads((proj / "data/source.json").read_text("utf-8"))
    src = proj / src_meta.get("file", "input/source.mp4")
    cap_path = proj / "data/captions.json"
    caps = json.loads(cap_path.read_text("utf-8"))
    if not src.exists():
        sys.exit(f"source clip not found: {src} (a broken --link symlink?)")
    loud, thr = loudness(src, a.fps)
    rows = measure(caps, loud, a.fps, a.win, a.min_sil, a.run)
    ok, txt = report(rows, a.fps, thr, a.start_tol, a.end_tol)
    print(txt)
    if a.fix:
        bak = proj / "data/captions.before-sync.json"
        if not bak.exists():
            shutil.copy2(cap_path, bak)
        moved = fix(caps, rows, a.fps)
        cap_path.write_text(json.dumps(caps, ensure_ascii=False, indent=1), "utf-8")
        (proj / "data/transcript.txt").write_text(
            "\n".join(f"{c['t0']:7.2f}-{c['t1']:7.2f}  {c['zh']}" for c in caps) + "\n", "utf-8")
        print(f"\n--fix: moved {moved} line edges (backup {bak.name}); re-checking:\n")
        rows = measure(caps, loud, a.fps, a.win, a.min_sil, a.run)
        ok, txt = report(rows, a.fps, thr, a.start_tol, a.end_tol)
        print(txt)
    if a.json:
        Path(a.json).write_text(json.dumps(dict(ok=ok, threshold=thr, rows=rows), ensure_ascii=False, indent=1),
                                "utf-8")
    sys.exit(0 if ok else (2 if ok is None else 1))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Chinese text on a Windows console or pipe
    main()
