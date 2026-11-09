"""Pre-delivery checklist: measure the rendered file and the storyboard, print a ✓/✗ table, write out/qc.md.

    python tools/qc.py projects/my-video                         # newest .mp4 in <project>/out
    python tools/qc.py projects/my-video --video out/x.mp4

Checks are measured from real files, never from memory (ported from talking-video-skills' self-check list):
  size/aspect   output aspect = source aspect (preview is half size, master full size)
  duration      |video - source| <= max(0.05 s, 2 frames) and |audio - video| <= 0.05 s
  loudness      integrated within +-1 LU of timeline.TARGET_LUFS, true peak <= -1 dBTP
  fresh         the render is newer than timeline.py, scenes.py and data/captions.json
  sfx density   <= 0.8 events per second overall, and no two of the same kind within 0.25 s
  presenter     no 'hidden' stretch longer than 10 s (viewers want the face back)
  captions      caption sync vs waveform (tools/check_sync.py): starts within +-3 frames
Exit code 1 when anything fails; failures are reported as they are, never rounded into a pass.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT))


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,duration,r_frame_rate"
                        ":format=duration", "-of", "json", str(path)], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def ebur128(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0",
                        "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    tail = r.stderr[r.stderr.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", tail)
    p = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", tail)
    return (float(i.group(1)) if i else None), (float(p.group(1)) if p and p.group(1) != "-inf" else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--video", default=None)
    a = ap.parse_args()

    from wbx.render import Project
    P = Project(a.project)
    tl = P.timeline
    if a.video:
        vid = Path(a.video) if Path(a.video).is_absolute() else (P.dir / a.video)
    else:
        mp4s = [p for p in (P.dir / "out").glob("*.mp4") if not p.name.startswith("_")]
        if not mp4s:
            sys.exit("no rendered .mp4 in out/ — render a preview first")
        vid = max(mp4s, key=lambda p: p.stat().st_mtime)
    rows = []

    def add(name, ok, value, want):
        rows.append((name, ok, value, want))

    info = probe(vid)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    au = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    sw, sh = P.src["width"], P.src["height"]
    w, h = int(v["width"]), int(v["height"])
    add("size / aspect", abs(w / h - sw / sh) < 0.01, f"{w}x{h} ({w / sw:.2f}x source)", f"aspect of {sw}x{sh}")
    vd = float(v.get("duration") or info["format"]["duration"])
    num, den = (v.get("r_frame_rate") or "30/1").split("/")
    vfps = float(num) / float(den or 1)
    tol = max(0.05, 2.0 / vfps)                       # whole frames: the last partial frame cannot exist
    add("duration vs source", abs(vd - P.duration) <= tol, f"{vd:.3f} s vs {P.duration:.3f} s",
        f"diff <= {tol:.3f} s (2 frames)")
    if au:
        ad = float(au.get("duration") or vd)
        add("audio vs video", abs(ad - vd) <= 0.05, f"{ad:.3f} s vs {vd:.3f} s", "diff <= 0.05 s")
        target = float(getattr(tl, "TARGET_LUFS", -14.0))
        lufs, peak = ebur128(vid)
        add("loudness", lufs is not None and abs(lufs - target) <= 1.0, f"{lufs} LUFS", f"{target:g} +-1 LU")
        add("true peak", peak is not None and peak <= -1.0, f"{peak} dBTP", "<= -1 dBTP")
    else:
        add("audio track", False, "none", "voice + sfx")

    newest = max((P.dir / f).stat().st_mtime for f in ("timeline.py", "scenes.py", "data/captions.json"))
    add("render is fresh", vid.stat().st_mtime >= newest, "newer than edits" if vid.stat().st_mtime >= newest
        else "OLDER than the last edit", "render after the last change")

    ev = sorted(tl.sfx_events(), key=lambda e: e[1]) if hasattr(tl, "sfx_events") else []
    dens = len(ev) / max(P.duration, 1e-6)
    add("sfx density", dens <= 0.8, f"{len(ev)} events, {dens:.3f}/s", "<= 0.8/s")
    last, clash = {}, []
    for kind, t in ev:
        if kind in last and t - last[kind] < 0.25:
            clash.append(f"{kind}@{t:.2f}")
        last[kind] = t
    add("sfx same-kind spacing", not clash, ", ".join(clash[:5]) or "ok", ">= 0.25 s apart")

    pres = list(P.presenter) + [(P.duration, "end")]
    longest, at_t = 0.0, None
    for (t0, st), (t1, _) in zip(pres, pres[1:]):
        if st == "hidden" and t1 - t0 > longest:
            longest, at_t = t1 - t0, t0
    add("presenter hidden stretch", longest <= 10.0,
        f"{longest:.1f} s" + (f" from {at_t:.1f} s" if at_t is not None else ""), "<= 10 s")

    r = subprocess.run([sys.executable, str(KIT / "tools/check_sync.py"), str(P.dir)], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    m = re.search(r"start: (n=.*?)\s{3}", r.stdout)
    if r.returncode == 2:
        add("caption sync", None, "not measurable (no silences in the audio); check by ear", "starts +-3 f, ends +-6 f")
    else:
        add("caption sync", r.returncode == 0, m.group(1) if m else (r.stdout.strip().splitlines() or ["?"])[-1],
            "starts +-3 f, ends +-6 f")

    out = [f"# QC: {vid.name}", "", "| check | | measured | target |", "|---|---|---|---|"]
    out += [f"| {n} | {'–' if ok is None else '✓' if ok else '✗'} | {val} | {want} |" for n, ok, val, want in rows]
    fails = [n for n, ok, _, _ in rows if ok is False]
    unchecked = [n for n, ok, _, _ in rows if ok is None]
    out += ["", f"**{'PASS' if not fails else 'FAIL: ' + ', '.join(fails)}**"
            + (f"  (not checked: {', '.join(unchecked)})" if unchecked else "")]
    if r.returncode == 1:
        out += ["", "```", r.stdout.strip(), "```"]
    txt = "\n".join(out)
    (P.dir / "out").mkdir(exist_ok=True)
    (P.dir / "out/qc.md").write_text(txt + "\n", "utf-8")
    print(txt)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Chinese text on a Windows console or pipe
    main()
