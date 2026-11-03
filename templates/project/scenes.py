"""Scenes for this video — starter. Each scene is fn(c, t); times come from timeline.T.

Authoring spaces (see wbx/layout.py): stage scenes use x 0..1080, y 320..1260 (auto-fitted to any aspect);
lower-third ("over") scenes use a 1080x1440 reference with text at y ~980..1320 (anchored to the bottom).
Headers inside stage scenes: `with frame(c): ...` at X0=64, y 118 (kicker) / 196 (title).
"""
from types import SimpleNamespace

from wbx.components import annotate_text, callout, confetti, counter, stamp, sticky  # noqa: F401
from wbx.core import (AMBER, BLUE, CYAN, GREEN, INK, MARKER, MUTE, RED, burst, clamp01, draw_label,  # noqa: F401
                      draw_text, ease_out, glass, marker, sparkle, spring, squiggle, text_width)
from wbx.icons import icon_in
from wbx.scene import frame

from timeline import CAPTIONS, DURATION, T as _T

T = SimpleNamespace(**_T)
X0, X1 = 64, 1016


def title_over(c, t):
    line = CAPTIONS[0]["zh"].rstrip("，。！？,.!?")
    draw_label(c, "TOPIC", X0, 1080, 26, BLUE, t=t, t0=0.1)
    w = draw_text(c, line, X0, 1200, 96, 800, INK, t=t, t0=0.05, stagger=0.06, style="bounce")
    squiggle(c, X0, X0 + w, 1236, ease_out((t - 0.8) / 0.6), MARKER, 1, 5, 8, 30)
    sparkle(c, X0 + w + 40, 1100, 24, t, 0.9)


def point(c, t):
    with frame(c):
        draw_label(c, "KEY POINT", X0, 118, 26, BLUE, t=t, t0=T.point)
        draw_text(c, "要点", X0, 196, 64, 700, INK, t=t, t0=T.point + 0.08)
    icon_in(c, "bulb", 540, 560, 200, t, T.point + 0.2)
    line = next(l for l in CAPTIONS if l["t0"] >= T.point)["zh"].rstrip("，。！？,.!?")
    glass(c, X0, 760, X1 - X0, 220, 36)
    draw_text(c, line, 540, 890, 52, 700, INK, "center", t=t, t0=T.point + 0.4)


def outro_over(c, t):
    line = CAPTIONS[-1]["zh"].rstrip("，。！？,.!?")
    w1 = text_width(line, 84, 800)
    marker(c, X0 - 10, 1150, w1 + 24, 48, ease_out((t - T.outro - 0.6) / 0.6))
    draw_text(c, line, X0, 1200, 84, 800, INK, t=t, t0=T.outro, stagger=0.06, style="bounce")
    confetti(c, X0 + w1 * 0.6, 1120, t, T.outro + 0.9)


SCENES = [
    dict(t0=0.0, t1=T.point - 0.35, layer="over", fn=title_over),
    dict(t0=T.point - 0.3, t1=T.outro - 0.3, fn=point, enter="pop", flash=True),
    dict(t0=T.outro - 0.3, t1=DURATION + 5, layer="over", fn=outro_over),
]
