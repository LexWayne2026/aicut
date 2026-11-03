"""Sound: voice-over + music bed + whiteboard foley, all on the cues the visuals use.

- Voice: the original recording, cleaned (high-pass, gentle compression).
- Music: a CC0 track from music/ (project timeline.MUSIC, default "clouds"), faded in/out and side-chain
  ducked under the voice. Tracks: clouds, blue-skies, new-shoes, puppy-love (Holizna, CC0).
- Foley: synthesised here (deterministic, seeded): pencil scribbles, marker squeaks, paper slides,
  marimba pops, pen taps, soft knocks, rising arpeggios and a bell for each chapter.
- Master: loudness-normalised with a limiter (TARGET_LUFS; -12 for Douyin per the reference spec).
"""
import subprocess
import wave
from pathlib import Path

import numpy as np

KIT = Path(__file__).resolve().parent.parent
SR = 48000
TARGET_LUFS = -14.0       # project can override with timeline.TARGET_LUFS (-12 for Douyin)
MUSIC_DB = -10.0          # music bed level before ducking (timeline.MUSIC_DB overrides)
PENTA = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5]  # C major pentatonic for the pops


# ------------------------------------------------------------------ dsp helpers
def _t(dur):
    return np.arange(int(dur * SR)) / SR


def _ma(x, n):
    n = max(1, int(n))
    return np.convolve(x, np.ones(n) / n, mode="same")


def band(x, lo, hi):
    """Crude band-pass from two moving averages (vectorised, good enough for foley)."""
    return _ma(x, SR / hi) - _ma(x, SR / lo)


def env_ad(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1.0, t / max(a, 1e-4)) * np.exp(-t / d)


def norm(x, peak=1.0):
    m = np.max(np.abs(x)) or 1.0
    return x / m * peak


# ------------------------------------------------------------------ foley
def marimba(f, dur=0.45, bright=0.35):
    t = _t(dur)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.18)
    s += bright * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t / 0.035)
    s += 0.15 * np.sin(2 * np.pi * f * 9.2 * t) * np.exp(-t / 0.012)
    return s * np.minimum(1, t / 0.0015)


def pop(rng, i):
    f = PENTA[i % len(PENTA)] * (0.5 if i % 7 == 3 else 1.0)
    return norm(marimba(f), 0.9)


def tick(rng, i):
    t = _t(0.07)
    noise = band(rng.standard_normal(len(t)), 1500, 6000)
    body = np.sin(2 * np.pi * 1850 * t) * np.exp(-t / 0.01)
    return norm((norm(noise) * 0.6 + body) * env_ad(len(t), 0.0008, 0.012), 0.8)


def scribble(rng, i):
    """Pencil on paper: grainy band-limited noise, gated by quick back-and-forth strokes."""
    dur = 0.42 + 0.1 * rng.random()
    t = _t(dur)
    grain = band(rng.standard_normal(len(t)), 2200, 9000)
    rate = 11 + 4 * rng.random()
    strokes = np.abs(np.sin(np.pi * rate * t + rng.random() * 3)) ** 0.6
    shape = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.5
    crackle = (rng.random(len(t)) > 0.996) * rng.standard_normal(len(t)) * 3
    return norm((grain * strokes + band(crackle, 2000, 9000)) * shape, 0.8)


def marker(rng, i):
    """Felt marker swipe: softer, lower band with a faint squeak."""
    dur = 0.55
    t = _t(dur)
    noise = band(rng.standard_normal(len(t)), 900, 4500)
    squeak = np.sin(2 * np.pi * (1650 + 120 * np.sin(2 * np.pi * 3 * t)) * t) * 0.08
    shape = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.7 * (0.85 + 0.15 * np.sin(2 * np.pi * 7 * t))
    return norm((norm(noise) + squeak) * shape, 0.8)


def paper(rng, i):
    """Card sliding onto the board."""
    dur = 0.38
    t = _t(dur)
    noise = band(rng.standard_normal(len(t)), 400, 5000)
    shape = (t / dur) ** 0.8 * np.exp(-((t / dur - 0.55) ** 2) / 0.06)
    thud = np.sin(2 * np.pi * 140 * t) * np.exp(-np.maximum(0, t - 0.28) / 0.03) * (t > 0.28) * 0.6
    return norm(norm(noise * shape) + thud, 0.8)


def swish(rng, i):
    """Photo flying across the board (presenter morph)."""
    dur = 0.65
    t = _t(dur)
    x = rng.standard_normal(len(t))
    lo = band(x, 250, 1500)
    hi = band(x, 1500, 7000)
    p = np.clip(t / dur, 0, 1)
    mixk = np.sin(np.pi * p)
    shape = np.sin(np.pi * p) ** 2
    return norm((norm(lo) * (1 - mixk) + norm(hi) * mixk) * shape, 0.8)


def deny(rng, i):
    """Two soft wooden knocks."""
    out = np.zeros(int(0.3 * SR))
    for k, (f, off) in enumerate(((196.0, 0.0), (164.8, 0.11))):
        s = marimba(f, 0.18, 0.15)
        o = int(off * SR)
        out[o:o + len(s)] += s[: len(out) - o]
    return norm(out, 0.85)


def rise(rng, i):
    out = np.zeros(int(0.9 * SR))
    for k, f in enumerate((523.25, 659.25, 783.99, 1046.5)):
        s = marimba(f, 0.5, 0.3) * (0.7 + 0.1 * k)
        o = int(k * 0.085 * SR)
        out[o:o + len(s)] += s[: len(out) - o]
    return norm(out, 0.85)


def chime(rng, i):
    t = _t(2.2)
    s = sum(a * np.sin(2 * np.pi * 1046.5 * r * t) * np.exp(-t / d)
            for r, a, d in ((1.0, 0.6, 0.9), (2.0, 0.25, 0.5), (2.76, 0.18, 0.35), (5.4, 0.06, 0.15)))
    s += 0.35 * marimba(523.25, 2.2, 0.2)
    return norm(s * np.minimum(1, t / 0.003), 0.85)


def stamp(rng, i):
    """Rubber stamp: low thump + papery slap."""
    t = _t(0.35)
    thump = np.sin(2 * np.pi * (95 + 60 * np.exp(-t * 30)) * t) * np.exp(-t / 0.07)
    slap = band(rng.standard_normal(len(t)), 600, 6000) * np.exp(-t / 0.025)
    return norm(thump + norm(slap) * 0.6, 0.9)


def erase(rng, i):
    """Whiteboard eraser rub: rhythmic, soft, band-limited noise."""
    dur = 0.75
    t = _t(dur)
    rub = band(rng.standard_normal(len(t)), 300, 3500)
    gate = 0.55 + 0.45 * np.abs(np.sin(np.pi * 7 * t))
    shape = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.6
    return norm(rub * gate * shape, 0.8)


def flap(rng, i):
    """Sticky note slapped on: quick airy flap + tap."""
    t = _t(0.28)
    air = band(rng.standard_normal(len(t)), 500, 4000) * np.exp(-((t - 0.06) ** 2) / 0.0012)
    tap = np.sin(2 * np.pi * 420 * t) * np.exp(-np.maximum(0, t - 0.11) / 0.02) * (t > 0.11)
    return norm(norm(air) + 0.7 * tap, 0.85)


def draw(rng, i):
    """Longer pencil drawing an icon (~0.9 s)."""
    dur = 0.9
    t = _t(dur)
    grain = band(rng.standard_normal(len(t)), 2400, 9000)
    strokes = np.abs(np.sin(np.pi * (5 + 2 * rng.random()) * t)) ** 0.8
    shape = np.minimum(1, t / 0.05) * np.minimum(1, (dur - t) / 0.15)
    return norm(grain * strokes * shape, 0.7)


SYNTH = dict(stamp=stamp, erase=erase, flap=flap, draw=draw, pop=pop, tick=tick, scribble=scribble, marker=marker, paper=paper, swish=swish, deny=deny,
             rise=rise, chime=chime)
LEVEL_DB = dict(stamp=-12, erase=-18, flap=-16, draw=-19, pop=-13, tick=-17, scribble=-15, marker=-17, paper=-16, swish=-16, deny=-13, rise=-14, chime=-14)


def build_sfx(events, start, end):
    n = int((end - start) * SR) + SR
    buf = np.zeros(n)
    for i, (kind, t) in enumerate(sorted(events, key=lambda e: e[1])):
        if not (start - 2 <= t < end):
            continue
        rng = np.random.default_rng(1000 + i)           # deterministic per event, varied between events
        s = SYNTH[kind](rng, i) * 10 ** (LEVEL_DB[kind] / 20)
        lead = {"swish": 0.3, "paper": 0.2, "marker": 0.05, "flap": 0.05}.get(kind, 0.0)
        off = int((t - start - lead) * SR)
        a, b = max(0, off), min(n, off + len(s))
        if b > a:
            buf[a:b] += s[a - off:b - off]
    # light stereo spread: a few ms delay on the right channel
    d = int(0.004 * SR)
    right = np.concatenate([np.zeros(d), buf[:-d]])
    return np.clip(np.stack([buf, right * 0.92 + buf * 0.08], 1), -1, 1)


def write_wav(path, data):
    pcm = (data * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def build_mix(P, start, end):
    """P is the render Project (needs .dir, .video, .timeline)."""
    tl = P.timeline
    out = P.dir / "out"
    out.mkdir(exist_ok=True)
    events = tl.sfx_events() if hasattr(tl, "sfx_events") else []
    sfx = out / "_sfx.wav"
    write_wav(sfx, build_sfx(events, start, end))
    mix = out / "_mix.wav"
    music = KIT / "music" / f"{getattr(tl, 'MUSIC', 'clouds')}.mp3"
    mdb = getattr(tl, "MUSIC_DB", MUSIC_DB)
    lufs = getattr(tl, "TARGET_LUFS", TARGET_LUFS)
    dur = end - start
    fo = max(0.0, dur - 3.5)
    voice = (f"[0:a]atrim={start}:{end},asetpts=PTS-STARTPTS,aresample={SR},highpass=f=70,"
             f"acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120,asplit=2[v][vkey];")
    if music.exists() and getattr(tl, "MUSIC", "clouds"):
        flt = (voice +
               f"[2:a]aloop=loop=-1:size=2e9,atrim={start}:{start + dur + 0.5},asetpts=PTS-STARTPTS,aresample={SR},volume={mdb}dB,"
               f"afade=t=in:st=0:d=1.5,afade=t=out:st={fo:.3f}:d=3.5[m0];"
               f"[m0][vkey]sidechaincompress=threshold=0.035:ratio=5:attack=40:release=650:makeup=1[m];"
               f"[1:a]anull[s];[v][m][s]amix=inputs=3:normalize=0:duration=first,"
               f"loudnorm=I={lufs}:TP=-2:LRA=9,alimiter=limit=0.79:level=false[o]")
        ins = ["-i", str(P.video), "-i", str(sfx), "-i", str(music)]
    else:
        flt = (voice + f"[vkey]anullsink;[1:a]anull[s];[v][s]amix=inputs=2:normalize=0:duration=first,"
               f"loudnorm=I={lufs}:TP=-2:LRA=9,alimiter=limit=0.79:level=false[o]")
        ins = ["-i", str(P.video), "-i", str(sfx)]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", flt, "-map", "[o]", "-ar", str(SR),
                    str(mix)], check=True)
    return mix
