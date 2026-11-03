"""Template 3 (Soft Glass) scenes: each scene is fn(c, t) in the 1080x1440 reference space (auto-fitted to any aspect).
Stage scenes sit on the lavender ground under the presenter, "over" scenes above it. Keep cards few: type and glass
on the ground carry most of the layout. See references/template-3-softglass.md."""
from wbx.softglass import (ACCENT, G1, G2, MUTE, NAVY, SOFTS, WHITE, around, bar, button, card, glass, glass_pill,  # noqa: F401
                           grad, orb, outline, pop, pulse, ripple, rise, roll, slide, spring, text, text_w)

from timeline import CAPTIONS, DURATION, T


def clean(s):
    return s.rstrip("，。！？,.!?")


def hook_over(c, t):
    line = clean(CAPTIONS[0]["zh"])
    rise(c, t, .05, 540, 1060, lambda: text(c, line, 540, 1100, 96, WHITE, "c"), dy=60)


def point(c, t):
    t0 = T["point"]
    line = clean(next(l for l in CAPTIONS if l["t0"] >= t0)["zh"])
    rise(c, t, t0 + .2, 540, 160, lambda: text(c, "第一点", 270, 156, 32, MUTE, wt="m"), dy=24)
    rise(c, t, t0 + .3, 540, 560, lambda: text(c, line, 540, 600, 84, NAVY, "c"), dy=60)
    rise(c, t, t0 + .5, 540, 760, lambda: orb(c, 540, 800, 90, SOFTS[0], "tablet"), dy=60)


def outro_over(c, t):
    line = clean(CAPTIONS[-1]["zh"])
    rise(c, t, T["outro"] + .1, 540, 1130, lambda: glass_pill(c, 540, 1130, line, 48), dy=40)


SCENES = [
    dict(t0=0.0, t1=T["point"], layer="over", fn=hook_over),
    dict(t0=T["point"], t1=T["outro"], fn=point),
    dict(t0=T["outro"], t1=DURATION + 5, layer="over", fn=outro_over),
]
