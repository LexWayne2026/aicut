"""Template 2 demo cue sheet (fish-oil demo script). Every time comes from the voice-over."""
from wbx.cues import CAPTIONS, DURATION, at  # noqa: F401

TEMPLATE = 2              # 1 = whiteboard, 2 = Pop Card
MUSIC = None              # Template 2 default: sound effects only
TARGET_LUFS = -14.0

T = dict(
    hook_end=at("而进口的一瓶", end=True) + .5,
    dose=at("普通的一粒含有"),
    need=at("如果每天想补充"),
    dose_end=at("所以先看含量"),
    forms=at("同样的鱼油"),
    move=at("可以做成软胶囊", "软") - .3,
    forms_end=at("选一种你吃得下去的", end=True) + .2,
)

# presenter is always live video. A slot is "full", "hidden", a name from popcard.SLOTS
# (tl tr bl br center left right), or (x, y, w, h[, rot]) in the 1080x1440 reference space.
PRESENTER = [
    (0.0, "full"),
    (T["dose"] + .1, "tl"),
    (T["need"], "tr"),
    (T["dose_end"], "full"),
    (T["forms"], "center"),
    (T["move"], "bl"),
    (T["forms_end"], "full"),
]

CAPTION_MUTE = [(0.0, T["hook_end"])]


def sfx_events():
    t300, t900 = at("普通的一粒含有", "300"), at("如果每天想补充", "900")
    ev = [("tick", .3), ("tick", .55), ("pop", at("超市里的", "超市")), ("pop", at("超市里的", "几十")),
          ("pop", at("而进口的一瓶", "进口")), ("stamp", at("而进口的一瓶", "好几百")),
          ("swish", T["dose"] + .3), ("swish", T["need"] + .25), ("pop", t300), ("stamp", t900),
          ("rise", at("普通的就要吃三粒", "三粒")), ("pop", at("高浓度的可能", "高浓度")), ("stamp", at("高浓度的可能", "一粒")),
          ("swish", T["dose_end"] + .25), ("swish", T["forms"] + .05), ("stamp", T["forms"] + .02), ("swish", T["move"] + .3),
          ("swish", T["forms_end"] + .25)]
    for cue in [("可以做成软胶囊", "软胶囊"), ("小粒胶囊",), ("肠溶胶囊",), ("乳液",), ("软糖或者是液体", "软糖"), ("软糖或者是液体", "液体")]:
        ev.append(("pop", at(*cue, after=T["forms"])))
    return ev
