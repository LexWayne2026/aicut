"""Scene runner — a TransitionSeries-like timeline for the whiteboard renderer.

A project's scenes.py exports SCENES, a list of dicts (or legacy 4-tuples (t0, t1, layer, fn)):

    dict(t0=..., t1=..., fn=draw_fn,
         layer="stage" | "over",        # stage = on the board (presenter is the corner photo or hidden)
                                        # over  = lower-third over the full-frame presenter
         space="stage" | "frame" | "lower",   # authoring coordinates (default: stage for stage, lower for over)
         enter=None | "slide-left" | "slide-right" | "slide-up" | "wipe" | "iris" | "flip" | "page" | "pop",
         enter_dur=0.55,
         exit="blur" | <same kinds> | None, exit_dur=0.45,
         camera=True,                   # slow push-in + drift while the scene is on (stage space only)
         flash=False)                   # warm paper light-leak overlay at the scene's start (cut point)

`fn(c, t)` draws the scene at absolute time t; times inside come from cues (never hard-code seconds).
Inside a stage-space scene, use `with frame(c):` to draw something in frame coordinates (e.g. a header).
"""
import math
from contextlib import contextmanager

from . import layout as L
from .components import flash, presentation
from .core import EXPO_OUT, SMOOTH, clamp01, layer, out_env

EXIT = 0.45


@contextmanager
def frame(c):
    """Temporarily draw in FRAME coordinates from inside a stage/lower scene."""
    c.save()
    L.to_frame(c)
    try:
        yield
    finally:
        c.restore()


def _norm(sc):
    if isinstance(sc, dict):
        d = dict(sc)
    else:
        t0, t1, lay, fn = sc[:4]
        d = dict(t0=t0, t1=t1, layer=lay, fn=fn)
    d.setdefault("layer", "stage")
    d.setdefault("space", "stage" if d["layer"] == "stage" else "lower")
    d.setdefault("enter", None)
    d.setdefault("enter_dur", 0.55)
    d.setdefault("exit", "blur")
    d.setdefault("exit_dur", EXIT)
    d.setdefault("camera", d["space"] == "stage")
    d.setdefault("flash", False)
    return d


def draw_scenes(c, t, scenes, which):
    lay = L.current()
    for raw in scenes:
        s = _norm(raw)
        if s["layer"] != which:
            continue
        t0, t1 = s["t0"], s["t1"]
        if t < t0 - 0.05 or t > t1 + s["exit_dur"]:
            continue
        c.save()
        if s["space"] == "stage":
            lay.enter_stage(c)
            box = (0, 320, 1080, 1260)
        elif s["space"] == "lower":
            lay.enter_lower(c)
            box = (0, 860, 1080, 1440)
        else:
            box = (0, 0, lay.W, lay.H)
        if s["camera"]:
            # slow push-in with a little drift (Ken Burns), eased so it never feels mechanical
            d = max(0.5, t1 - t0)
            u = SMOOTH(clamp01((t - t0) / d))
            sc = 1.0 + 0.035 * u
            cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            c.translate(cx + 10 * math.sin(u * 2.2), cy - 6 * u)
            c.scale(sc, sc)
            c.translate(-cx, -cy)
        after = None
        c.save()                                   # presentation clip/transform lives in here
        if s["enter"] and t < t0 + s["enter_dur"]:
            pe = EXPO_OUT(clamp01((t - t0) / s["enter_dur"])) if s["enter"] != "wipe" else \
                clamp01((t - t0) / s["enter_dur"])
            after = presentation(c, s["enter"], pe, True, box)
        ex = s["exit"]
        if ex and ex != "blur" and t > t1:
            px = 1 - clamp01((t - t1) / s["exit_dur"])
            after = presentation(c, ex, px, False, box) or after
            e = 1.0
        else:
            e = out_env(t, t1, s["exit_dur"]) if ex == "blur" else (1.0 if t <= t1 else 0.0)
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        with layer(c, e, (1 - e) * 18, 1 - (1 - e) * 0.03, cx, cy) as vis:
            if vis:
                s["fn"](c, t)
        c.restore()
        if after:
            after(c)
        if s["flash"]:
            flash(c, t, t0, box)
        c.restore()
