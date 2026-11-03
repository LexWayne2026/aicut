"""Cue sheet for this video. EVERY time comes from the voice-over (data/captions.json) via at();
never hard-code seconds in scenes. Replace the starter cues below with the real storyboard beats.

    at("line text fragment")                 -> start of that caption line
    at("line text fragment", "word")         -> start of that word inside the line
    at("fragment", "word", end=True)         -> end of that word
    at("fragment", after=60)                 -> first match at/after 60 s (repeated phrases)
"""
from wbx.cues import CAPTIONS, DURATION, at, pauses  # noqa: F401

TEMPLATE = 1              # 1 = whiteboard, 2 = Pop Card
MUSIC = "clouds"          # clouds | blue-skies | new-shoes | puppy-love (CC0) — or None for no music
MUSIC_DB = -10.0
TARGET_LUFS = -14.0       # -12 for Douyin

L = CAPTIONS
T = dict(
    hook=L[0]["t0"],
    point=L[min(2, len(L) - 1)]["t0"],
    outro=L[-1]["t0"],
)

# presenter: "full" (fills the frame, lower-third text only), "pip" (taped photo top-right), "hidden"
PRESENTER = [
    (0.0, "full"),
    (T["point"] - 0.25, "pip"),
    (T["outro"] - 0.3, "full"),
]

# hide captions while an on-screen statement says the same words
CAPTION_MUTE = [(0.0, T["point"] - 0.1)]


def sfx_events():
    """(kind, time) — every visual event gets a sound. Kinds: pop tick scribble marker paper swish deny rise
    chime stamp erase flap draw."""
    ev = [("swish", t) for t, _ in PRESENTER[1:]]
    ev += [("draw", T["point"] + 0.2), ("chime", T["outro"])]
    return ev
