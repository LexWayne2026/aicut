"""Template 2 (Pop Card) cue sheet. EVERY time comes from the voice-over (data/captions.json) via at();
never hard-code seconds in scenes. Replace the starter cues with the real storyboard beats.

    at("line text fragment")                 -> start of that caption line
    at("line text fragment", "word")         -> start of that word inside the line
    at("fragment", after=60)                 -> first match at/after 60 s (repeated phrases)
"""
from wbx.cues import CAPTIONS, DURATION, at, pauses  # noqa: F401

TEMPLATE = 2              # 1 = whiteboard, 2 = Pop Card
MUSIC = None              # Template 2 default: sound effects only
TARGET_LUFS = -14.0       # -12 for Douyin

L = CAPTIONS
T = dict(
    point=L[min(2, len(L) - 1)]["t0"],
    outro=L[-1]["t0"],
)

# presenter is always live video. A slot is "full", "hidden", a name from popcard.SLOTS
# (tl tr bl br center left right), or (x, y, w, h[, rot]) in the 1080x1440 reference space.
PRESENTER = [
    (0.0, "full"),
    (T["point"] + .1, "tr"),
    (T["outro"], "full"),
]

# hide captions while an on-screen statement says the same words
CAPTION_MUTE = [(0.0, T["point"])]


def sfx_events():
    """(kind, time): every visual event gets a sound. Kinds: pop tick swish rise stamp chime paper flap deny."""
    return [("swish", T["point"] + .3), ("stamp", T["point"]), ("pop", T["point"] + .4), ("swish", T["outro"] + .25), ("chime", T["outro"] + .3)]
