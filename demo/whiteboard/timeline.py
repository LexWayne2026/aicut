"""Template 1 demo cue sheet (fish-oil demo script). Every time comes from the voice-over (data/captions.json)."""
from wbx.cues import CAPTIONS, DURATION, at  # noqa: F401

TEMPLATE = 1
MUSIC = "clouds"        # music/<name>.mp3 (CC0)
MUSIC_DB = -10.0
TARGET_LUFS = -14.0

T = dict(
    super_=at("超市里的", "超市"),
    tens=at("超市里的", "几十"),
    imported=at("而进口的一瓶", "进口"),
    hundreds=at("而进口的一瓶", "好几百"),
    dose=at("普通的一粒含有"),
    d300=at("普通的一粒含有", "300"),
    omega=at("普通的一粒含有", "Omega"),
    need=at("如果每天想补充"),
    d900=at("如果每天想补充", "900"),
    three=at("普通的就要吃三粒", "三粒"),
    conc=at("高浓度的可能", "高浓度"),
    one=at("高浓度的可能", "一粒"),
    check=at("所以先看含量"),
    price=at("所以先看含量", "再看"),
    forms=at("同样的鱼油"),
    f_soft=at("可以做成软胶囊", "软胶囊"),
    f_mini=at("小粒胶囊"),
    f_enteric=at("肠溶胶囊"),
    f_emul=at("乳液"),
    f_gummy=at("软糖或者是液体", "软糖"),
    f_liquid=at("软糖或者是液体", "液体"),
    pick=at("选一种你吃得下去的"),
    outro=at("关注我"),
)

# "full" fills the frame (lower-third text only), "pip" is the taped photo top-right, "hidden" shrinks away.
PRESENTER = [
    (0.0, "full"),
    (T["super_"] - 0.25, "pip"),
    (T["check"] - 0.15, "full"),
    (T["forms"] - 0.2, "pip"),
    (T["outro"] - 0.3, "full"),
]

CAPTION_MUTE = [(0.0, T["super_"] - 0.1), (T["check"], T["forms"] - 0.1)]


def sfx_events():
    ev = [("swish", t) for t, _ in PRESENTER[1:]]
    for k in ("super_", "imported", "d300", "conc", "f_soft", "f_mini", "f_enteric", "f_emul", "f_gummy", "f_liquid"):
        ev.append(("pop", T[k]))
    for k in ("tens", "hundreds"):
        ev.append(("draw", T[k] - 0.1))
    ev += [("rise", T["hundreds"]), ("tick", T["d900"]), ("rise", T["three"]), ("rise", T["one"]),
           ("marker", T["check"] + 0.7), ("scribble", T["price"] + 0.3), ("paper", T["forms"] - 0.05),
           ("erase", T["dose"] - 0.25), ("chime", T["outro"]), ("pop", T["pick"])]
    for i in range(3):
        ev.append(("pop", T["three"] - 0.4 + i * 0.2))
    return sorted(ev, key=lambda e: e[1])
