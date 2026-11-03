"""Template 3 demo cue sheet (fish-oil demo script). Every time comes from the voice-over."""
from wbx.cues import CAPTIONS, DURATION, at  # noqa: F401

TEMPLATE = 3              # 1 = whiteboard, 2 = Pop Card, 3 = Soft Glass
MUSIC = None              # Template 3 default: sound effects only
TARGET_LUFS = -14.0

T = dict(
    hook_end=at("而进口的一瓶", end=True) + .5,
    dose=at("普通的一粒含有"),
    chart=at("普通的就要吃三粒") - .35,
    dose_end=at("所以先看含量"),
    forms=at("同样的鱼油"),
    move=at("可以做成软胶囊", "软") - .3,
    forms_end=at("选一种你吃得下去的", end=True) + .2,
)

# presenter is always live video. A slot is "full", "hidden", a name from softglass.SLOTS
# (hero center avatar avatar_r tl tr bl br left right), or (x, y, w, h[, radius[, crop]]) in the 1080x1440 reference space.
PRESENTER = [
    (0.0, "full"),
    (T["dose"] + .12, "hero"),
    (T["chart"], "avatar"),
    (T["dose_end"], "full"),
    (T["forms"], "center"),
    (T["move"], "avatar"),
    (T["forms_end"], "full"),
]

CAPTION_MUTE = [(0.0, T["hook_end"])]


def sfx_events():
    ev = [("pop", at("超市里的", "超市")), ("tick", at("超市里的", "几十")), ("pop", at("而进口的一瓶", "进口")),
          ("chime", at("而进口的一瓶", "好几百")),
          ("swish", T["dose"]), ("pop", T["dose"] + .35), ("tick", at("普通的一粒含有", "300")),
          ("chime", at("如果每天想补充", "900")), ("pop", T["chart"] + .15), ("rise", at("普通的就要吃三粒", "三")),
          ("chime", at("高浓度的可能", "一")), ("swish", T["dose_end"]), ("swish", T["forms"]), ("swish", T["forms_end"])]
    for _, cue, _ in FORM_CUES:
        tt = at(*cue, after=T["forms"])
        ev += [("pop", tt), ("tick", tt + .2)]
    return ev


# the six forms: (label, cue in the speech, glyph)
FORM_CUES = [("软胶囊", ("可以做成软胶囊", "软胶囊"), "capsule"), ("小粒胶囊", ("小粒胶囊",), "tablet"),
             ("肠溶胶囊", ("肠溶胶囊",), "coated"), ("乳液", ("乳液",), "lipo"),
             ("软糖", ("软糖或者是液体", "软糖"), "gummy"), ("液体", ("软糖或者是液体", "液体"), "drop")]
