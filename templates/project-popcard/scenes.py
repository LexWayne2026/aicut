"""Template 2 (Pop Card) scenes: each scene is fn(c, t) in the 1080x1440 reference space (auto-fitted to any aspect).
Stage scenes sit under the presenter, "over" scenes above it. See references/template-2-popcard.md."""
from wbx.popcard import (INK, LIME, PINK, VIOLET, WHITE, YELLOW, around, back_out, badge, burst, card, dome, drop_text,  # noqa: F401
                         idle, pill, pop, pulse, rays, spring, star, text, whip)

from timeline import CAPTIONS, DURATION, T


def clean(s):
    return s.rstrip("，。！？,.!?")


def hook_over(c, t):
    drop_text(c, clean(CAPTIONS[0]["zh"]), 540, 1100, 104, WHITE, t, .05, align="c", stag=.05, fall=240)
    pop(c, t, .6, 960, 960, lambda: star(c, 960, 960, 38, YELLOW), spin=180)


def point(c, t):
    t0 = T["point"]
    line = clean(next(l for l in CAPTIONS if l["t0"] >= t0)["zh"])
    pop(c, t, t0 + .1, 118, 130, lambda: badge(c, 118, 130, 96, "1"), spin=-90)
    sheet = spring(t - t0, 10, .46)
    dome(c, 520 + (1 - sheet) * 1040, bulge=80 + 50 * (1 - sheet))
    pop(c, t, t0 + .4, 540, 860, lambda: pill(c, 540, 860, line, 58, INK, WHITE, "c", padx=44, pady=30))
    burst(c, 540, 860, t, t0 + .4, PINK, r0=200, r1=420)


def outro_over(c, t):
    drop_text(c, clean(CAPTIONS[-1]["zh"]), 540, 1170, 88, WHITE, t, T["outro"], align="c", stag=.05, fall=200)


SCENES = [
    dict(t0=0.0, t1=T["point"], layer="over", fn=hook_over),
    dict(t0=T["point"], t1=T["outro"], bg=LIME, enter="slam", fn=point),
    dict(t0=T["outro"], t1=DURATION + 5, layer="over", fn=outro_over),
]
