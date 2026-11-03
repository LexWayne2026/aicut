"""Cues from the voice-over: every time in a project is derived from word-level timings.

captions.json format (written by tools/transcribe.py, hand-correctable):
  [{"id": "c000", "t0": 0.0, "t1": 1.37, "zh": "同样是维生素，",
    "highlight": {"units": [{"text": "同", "start": 0.0, "end": 0.38}, ...]}}, ...]
`zh` is the display text of the line (any language works; the key name is historical).

Usage in a project's timeline.py:
    from wbx.cues import at, CAPTIONS, DURATION
    T = dict(hook=at("同样是维生素"), otc=at("药店里的OTC", "OTC"), ...)
"""
import json
from pathlib import Path

CAPTIONS = []
DURATION = 0.0
PROJECT = None


def load(project_dir):
    """Called by the renderer before the project's modules are imported."""
    global CAPTIONS, DURATION, PROJECT
    PROJECT = Path(project_dir)
    CAPTIONS[:] = json.loads((PROJECT / "data/captions.json").read_text("utf-8"))
    src = PROJECT / "data/source.json"
    if src.exists():
        DURATION = float(json.loads(src.read_text("utf-8"))["duration"])
    else:
        DURATION = CAPTIONS[-1]["t1"] + 0.6 if CAPTIONS else 0.0
    globals()["DURATION"] = DURATION
    return CAPTIONS


def _line(sub, after=0.0):
    for ln in CAPTIONS:
        if sub in ln["zh"] and ln["t0"] >= after:
            return ln
    raise KeyError(f"no caption line contains {sub!r} (after {after}s) — check data/captions.json")


def at(line_sub, word=None, end=False, nth=0, after=0.0):
    """Start (or end) time of `word` inside the first caption line (at or after `after`) containing
    `line_sub`. Without `word`, the line's own start/end."""
    ln = _line(line_sub, after)
    if word is None:
        return ln["t1"] if end else ln["t0"]
    units = ln["highlight"]["units"]
    text = "".join(u["text"] for u in units)
    i = -1
    for _ in range(nth + 1):
        i = text.index(word, i + 1)
    j = i + len(word) - 1 if end else i
    pos = 0
    for u in units:
        if pos <= j < pos + len(u["text"]):
            return u["end"] if end else u["start"]
        pos += len(u["text"])
    raise KeyError(word)


def line_at(t):
    for ln in CAPTIONS:
        if ln["t0"] <= t < ln["t1"]:
            return ln
    return None


def pauses(min_gap=0.45):
    """Gaps between caption lines (natural cut points for scene changes): [(start, end), ...]."""
    out = []
    for a, b in zip(CAPTIONS, CAPTIONS[1:]):
        if b["t0"] - a["t1"] >= min_gap:
            out.append((a["t1"], b["t0"]))
    return out
