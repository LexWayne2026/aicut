"""Adaptive layout: the output frame matches the source footage (size + aspect ratio).

Design space: the frame's SHORT side is 1080 units. A 1080x1440 source gives a 1080x1440 design
space, 2160x3840 gives 1080x1920, 3840x2160 gives 1920x1080. The renderer scales design units to
real pixels (scale = source short side / 1080), so a 4K source renders at 4K.

Scenes are authored in fixed spaces, which the layout maps onto each frame:
  STAGE  — content area, authored as x 0..1080, y 320..1260 (the 3:4 reference frame's content
           band). It is uniformly scaled to fit the frame's free area (below the header,
           above the captions) and centred. In 3:4 it maps 1:1.
  LOWER  — lower-third text over the full-frame presenter, authored in a 1080x1440 reference frame
           (y ~900..1320); anchored to the bottom-left of the real frame.
  FRAME  — header / chapter titles / captions use real design-space coordinates (top-left based).
"""
import skia

STAGE_AUTHOR = skia.Rect.MakeLTRB(0, 320, 1080, 1260)
LOWER_REF_H = 1440
MARGIN = 64


class Layout:
    def __init__(self, src_w, src_h):
        short = min(src_w, src_h)
        self.k = 1080.0 / short                       # source px -> design units
        self.W = round(src_w * self.k)
        self.H = round(src_h * self.k)
        self.portrait = self.H >= self.W
        W, H = self.W, self.H
        # corner photo: 3:4, sized from the short side
        pw = 224 if self.portrait else 250
        self.pip = skia.Rect.MakeXYWH(W - MARGIN + 8 - pw, 46, pw, pw * 4 / 3)
        # free area for stage content
        top = 300 if self.portrait else 228
        bottom = H - (150 if self.portrait else 96)
        avail_w, avail_h = W, bottom - top
        s = min(avail_w / STAGE_AUTHOR.width(), avail_h / STAGE_AUTHOR.height(), 1.25)
        cw, ch = STAGE_AUTHOR.width() * s, STAGE_AUTHOR.height() * s
        self.stage_scale = s
        self.stage_box = skia.Rect.MakeXYWH((W - cw) / 2, top + (avail_h - ch) / 2, cw, ch)
        self.caption_y = H - (80 if self.portrait else 56)
        self.lower_dy = H - LOWER_REF_H                # LOWER authored y -> frame y

    # ---- transforms (apply on top of the canvas' base pixel scale)
    def enter_stage(self, c):
        """Map STAGE authoring coordinates onto the stage box."""
        b, s = self.stage_box, self.stage_scale
        c.translate(b.left(), b.top())
        c.scale(s, s)
        c.translate(-STAGE_AUTHOR.left(), -STAGE_AUTHOR.top())

    def enter_lower(self, c):
        c.translate(0, self.lower_dy)

    def stage_center(self):
        return STAGE_AUTHOR.centerX(), STAGE_AUTHOR.centerY()


_CUR = {"layout": Layout(1080, 1440), "base": None}


def current():
    return _CUR["layout"]


def set_current(layout):
    _CUR["layout"] = layout


def set_base_matrix(m):
    """The canvas matrix that maps design units to pixels (set by the renderer each frame)."""
    _CUR["base"] = m


def to_frame(c):
    """Inside a stage scene, switch the canvas to FRAME coordinates (e.g. for a header)."""
    if _CUR["base"] is not None:
        c.setMatrix(_CUR["base"])
