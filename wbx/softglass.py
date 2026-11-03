"""wbx.softglass: Template 3 "Soft Glass". Flat lavender ground with faint diagonal lines, few cards, frosted glass
that really blurs what is behind it, lilac-to-sky gradients, rounded geometric type, springy focus-pull motion.

Scenes are authored in a 1080x1440 reference space that is uniformly fitted into the real frame; the ground bleeds to
the frame edges. The presenter is live video in any slot (see references/template-3-softglass.md).
Every function is a pure function of time t. Templates 1 and 2 do not import this module.
"""
import math
from pathlib import Path

import skia

from wbx.core import load_typeface
from wbx.cues import CAPTIONS

ROOT = Path(__file__).resolve().parent.parent
W, H = 1080, 1440                    # reference space

BG_T = "#E7E6FB"                     # lavender ground, top
BG_B = "#DCDEF8"                     # lavender ground, bottom
NAVY = "#1B1D3F"                     # text
MUTE = "#8D90B2"                     # secondary text
TRACK = "#EDEDF7"                    # empty bar / progress track
WHITE = "#FFFFFF"
G1 = "#A28BF3"                       # lilac (gradient start)
G2 = "#5DBDE3"                       # sky (gradient end)
ACCENT = "#7A7CF0"                   # the one solid accent: active caption character, small marks
SOFTS = [("#C9B8FF", "#8EC9F5"), ("#FFB8D2", "#C8B4FF"), ("#9FE3D0", "#8CC4F7"),
         ("#FFD3A8", "#FFA9C6"), ("#B9C3FF", "#E2B5FF"), ("#9ED8F7", "#A8B6FF")]   # pastel pairs for orbs and side cards
FROST = .4                           # seconds the frame frosts over before a scene change
FOCUS = .6                           # seconds the next shot takes to come into focus


# ------------------------------------------------------------------ fonts: Outfit for Latin and numerals, Noto Sans SC for Chinese
FONT_FILES = {("la", "b"): "Outfit-SemiBold.ttf", ("la", "m"): "Outfit-Medium.ttf",
              ("zh", "b"): "NotoSansSC-Bold.ttf", ("zh", "m"): "NotoSansSC-Medium.ttf"}
_TF, _F = {}, {}


def font(script, wt, size):
    k = (script, wt, round(size, 2))
    if k not in _F:
        if (script, wt) not in _TF:
            _TF[script, wt] = load_typeface(ROOT / "fonts" / FONT_FILES[script, wt])
        f = skia.Font(_TF[script, wt], size)
        f.setSubpixel(True)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        f.setHinting(skia.FontHinting.kNone)
        _F[k] = f
    return _F[k]


def _f(ch, wt, size):
    return font("zh", wt, size) if ord(ch) >= 0x2E80 else font("la", wt, size)


# ------------------------------------------------------------------ paint
def col(h, a=1.0):
    h = h.lstrip("#")
    return skia.Color(int(h[:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(255 * max(0, min(1, a))))


def fill(h, a=1.0, blur=0):
    p = skia.Paint(AntiAlias=True, Color=col(h, a))
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def stroke(h, w, a=1.0):
    return skia.Paint(AntiAlias=True, Color=col(h, a), Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                      StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)


def lin(x0, y0, x1, y1, colors, pos=None):
    """colors: hex strings or (hex, alpha) pairs."""
    return skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [skia.Point(x0, y0), skia.Point(x1, y1)], [col(*c) if isinstance(c, tuple) else col(c) for c in colors], pos))


def rad(cx, cy, r, colors):
    return skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        skia.Point(cx, cy), r, [col(*c) if isinstance(c, tuple) else col(c) for c in colors]))


def grad(x0, y0, x1, y1, a=G1, b=G2):
    """The house gradient, lilac to sky. Use it as a fill or text paint."""
    return lin(x0, y0, x1, y1, [a, b])


def rrect(x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    return skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)


# ------------------------------------------------------------------ type
def text_w(s, size, wt="b", track=-.01):
    return sum(_f(ch, wt, size).measureText(ch) + size * track for ch in s) - size * track


def text(c, s, x, y, size, color=NAVY, align="l", wt="b", track=-.01, a=1.0, paint=None):
    """wt "b" = Outfit SemiBold / Noto Sans SC Bold, "m" = Medium. paint (e.g. grad(...)) overrides colour."""
    w = text_w(s, size, wt, track)
    x -= {"l": 0, "c": w / 2, "r": w}[align]
    p = paint or fill(color, a)
    for ch in s:
        f = _f(ch, wt, size)
        c.drawString(ch, x, y, f, p)
        x += f.measureText(ch) + size * track
    return w


def digit_w(size, wt="b", track=-.03):
    return font("la", wt, size).measureText("0") + size * track


def roll(c, frm, to, x, y, size, paint, t, t0, stag=.07, w=11, z=.55, wt="b", track=-.03):
    """Odometer: each digit column spins upward from its old digit to its new one on its own spring. frm None spins
    in from nothing; frm and to must have the same length. Left aligned at x; returns the width."""
    f_ = font("la", wt, size)
    cw = digit_w(size, wt, track)
    if t <= t0:
        if frm is None:
            return cw * len(to)
        to = frm
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(x - 10, y - size * .8, x + cw * len(to) + 10, y + size * .14), doAntiAlias=True)
    for i, b in enumerate(to):
        a = int(frm[i]) if frm else (int(b) + 4) % 10
        b = int(b)
        b += 10 if b < a else 0
        p = spring(t - t0 - i * stag, w, z) if t > t0 else 0
        pos = a + (b - a) * p
        lo = math.floor(pos)
        fr = pos - lo
        for k, dy in ((lo, -fr * size * 1.06), (lo + 1, (1 - fr) * size * 1.06)):
            g = str(k % 10)
            c.drawString(g, x + i * cw + (cw - f_.measureText(g) - size * track) / 2, y + dy, f_, paint)
    c.restore()
    return cw * len(to)


# ------------------------------------------------------------------ surfaces
def background(c, w=W, h=H):
    """Lavender ground with two soft glows and faint 45-degree lines. Drawn in frame space by the renderer."""
    k = min(w, h) / 1080
    c.drawRect(skia.Rect.MakeWH(w, h), lin(0, 0, 0, h, [BG_T, BG_B]))
    c.drawCircle(-80 * k, h + 40 * k, 760 * k, rad(-80 * k, h + 40 * k, 760 * k, [("#C6E6F7", .9), ("#C6E6F7", 0)]))
    c.drawCircle(w + 60 * k, 120 * k, 620 * k, rad(w + 60 * k, 120 * k, 620 * k, [("#D9CCFF", .8), ("#D9CCFF", 0)]))
    p = stroke(WHITE, 1.6 * k, .32)
    step = 52 * k
    x = -h
    while x < w + h:
        c.drawLine(x, 0, x - h, h, p)
        x += step


def glass(c, x, y, w, h, r, tint=WHITE, ta=.28, blur=22, rim=.55):
    """Frosted glass: blurs whatever is already drawn behind it, then a light tint, a top sheen and a hairline rim."""
    rr = rrect(x, y, w, h, r)
    c.save()
    c.clipRRect(rr, doAntiAlias=True)
    bounds, bf = skia.Rect.MakeXYWH(x, y, w, h), skia.ImageFilters.Blur(blur, blur)
    rec = skia.Canvas.SaveLayerRec(bounds, None, bf, 0)      # keep refs alive: a temporary here segfaults skia-python
    c.saveLayer(rec)
    c.drawPaint(fill(tint, ta))
    c.restore()
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h * .5), lin(0, y, 0, y + h * .5, [(WHITE, .18), (WHITE, 0)]))
    c.restore()
    c.drawRRect(rrect(x + 1, y + 1, w - 2, h - 2, r), stroke(WHITE, 2, rim))


def card(c, x, y, w, h, r=56):
    """Flat white card: no rim, only a whisper of shadow. Use sparingly: one main card per scene at most."""
    c.drawRRect(rrect(x + 16, y + 18, w - 32, h, r), fill("#5A5FB0", .07, 24))
    c.drawRRect(rrect(x, y, w, h, r), fill(WHITE))


def glass_pill(c, cx, cy, s, size=38, fg=WHITE, h=None, wt="m"):
    h = h or size * 2.1
    w = text_w(s, size, wt) + size * 1.5
    glass(c, cx - w / 2, cy - h / 2, w, h, h / 2)
    text(c, s, cx, cy + size * .36, size, fg, "c", wt)
    return w


def button(c, x, y, w, h, label=None, size=44):
    """Gradient pill button with a soft lilac glow. Draw your own content on it when label is None."""
    c.drawRRect(rrect(x + 20, y + 24, w - 40, h, h / 2), fill(G1, .3, 26))
    c.drawRRect(rrect(x, y, w, h, h / 2), grad(x, y, x + w, y + h))
    c.drawRRect(rrect(x, y, w, h / 2, h / 2), lin(0, y, 0, y + h / 2, [(WHITE, .22), (WHITE, 0)]))
    if label:
        text(c, label, x + w / 2, y + h / 2 + size * .36, size, WHITE, "c")


def orb(c, cx, cy, r, pair=(G1, G2), kind=None):
    """Gradient circle with a soft highlight and an optional white glyph."""
    c.drawCircle(cx, cy, r, grad(cx - r, cy - r, cx + r, cy + r, *pair))
    c.drawCircle(cx - r * .3, cy - r * .35, r * .7, rad(cx - r * .3, cy - r * .35, r * .7, [(WHITE, .45), (WHITE, 0)]))
    if kind:
        glyph(c, kind, cx, cy, r * 1.6, WHITE)


def bar(c, cx, top, bot, bw, h, hot=False, paint=None):
    """Rounded chart bar: an empty track from top to bot, filled from the bottom to height h. hot = gradient fill."""
    c.drawRRect(rrect(cx - bw / 2, top, bw, bot - top, bw / 2), fill(TRACK))
    if h > 0:
        h = max(h, bw * .4)
        c.drawRRect(rrect(cx - bw / 2, bot - h, bw, h, bw / 2),
                    paint or (grad(cx, bot - h, cx, bot, G2, G1) if hot else fill("#CFCBF6")))


def outline(c, x, y, w, h, r, width=4):
    """Gradient outline: the selection ring for a card or tile."""
    p = grad(x, y, x + w, y + h)
    p.setStyle(skia.Paint.kStroke_Style)
    p.setStrokeWidth(width)
    c.drawRRect(rrect(x, y, w, h, r), p)


def chevrons(c, xl, xr, y, size=16):
    for sx, d in ((xl, 1), (xr, -1)):
        c.drawLine(sx + d * size * .75, y - size, sx, y, stroke(MUTE, 3))
        c.drawLine(sx, y, sx + d * size * .75, y + size, stroke(MUTE, 3))


def glyph(c, kind, cx, cy, s, color=WHITE, line=False):
    """Monoline icons sized to a tile of side s: tablet capsule coated lipo gummy drop bottle swap hex up."""
    lw = s * (.055 if line else .07)
    c.save()
    c.translate(cx, cy)
    sp, fp = stroke(color, lw), fill(color)
    if kind == "tablet":
        c.drawCircle(0, 0, s * .26, sp)
        c.rotate(-35)
        c.drawLine(-s * .17, 0, s * .17, 0, sp)
    elif kind == "capsule":
        c.rotate(-40)
        rr_ = rrect(-s * .32, -s * .14, s * .64, s * .28, s * .14)
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(-s, -s, s, 2 * s))
        c.drawRRect(rr_, fp)
        c.restore()
        c.drawRRect(rr_, sp)
    elif kind == "coated":
        c.drawCircle(0, 0, s * .17, fp)
        c.drawCircle(0, 0, s * .29, sp)
    elif kind == "lipo":
        c.drawCircle(0, 0, s * .1, fp)
        for i in range(9):
            a = i / 9 * math.tau
            c.drawCircle(s * .25 * math.cos(a), s * .25 * math.sin(a), s * .05, fp)
    elif kind == "gummy":
        for ex in (-.13, .13):
            c.drawCircle(s * ex, -s * .23, s * .07, fp)
        c.drawCircle(0, -s * .13, s * .14, fp)
        c.drawRRect(rrect(-s * .18, -s * .04, s * .36, s * .33, s * .15), fp)
    elif kind == "drop":
        p = skia.Path()
        p.moveTo(0, -s * .32)
        p.cubicTo(s * .1, -s * .16, s * .25, -s * .02, s * .25, s * .12)
        p.cubicTo(s * .25, s * .27, s * .13, s * .34, 0, s * .34)
        p.cubicTo(-s * .13, s * .34, -s * .25, s * .27, -s * .25, s * .12)
        p.cubicTo(-s * .25, -s * .02, -s * .1, -s * .16, 0, -s * .32)
        c.drawPath(p, fp)
    elif kind == "bottle":
        c.drawRRect(rrect(-s * .13, -s * .33, s * .26, s * .1, s * .03), fp)
        c.drawRRect(rrect(-s * .2, -s * .19, s * .4, s * .51, s * .1), sp)
        c.drawLine(-s * .2, s * .02, s * .2, s * .02, sp)
        c.drawLine(-s * .2, s * .14, s * .2, s * .14, sp)
    elif kind == "swap":
        for dx, dn in ((-.1, False), (.1, True)):
            y0, y1 = (-.22, .22) if dn else (.22, -.22)
            e = -.08 if dn else .08
            c.drawLine(s * dx, s * y0, s * dx, s * y1, sp)
            c.drawLine(s * dx, s * y1, s * (dx - .08), s * (y1 + e), sp)
            c.drawLine(s * dx, s * y1, s * (dx + .08), s * (y1 + e), sp)
    elif kind == "hex":
        p = skia.Path()
        for i in range(6):
            a = math.radians(60 * i + 30)
            (p.moveTo if i == 0 else p.lineTo)(s * .26 * math.cos(a), s * .26 * math.sin(a))
        p.close()
        c.drawPath(p, sp)
        c.drawCircle(0, 0, s * .09, sp)
    elif kind == "up":
        c.drawLine(0, s * .2, 0, -s * .2, sp)
        c.drawLine(0, -s * .2, -s * .13, -s * .07, sp)
        c.drawLine(0, -s * .2, s * .13, -s * .07, sp)
    c.restore()


# ------------------------------------------------------------------ motion
def spring(t, w=17.0, z=.36):
    if t <= 0:
        return 0.0
    wd = w * math.sqrt(1 - z * z)
    return 1 - math.exp(-z * w * t) * (math.cos(wd * t) + z * w / wd * math.sin(wd * t))


def d(fn, t, h=.004):
    return (fn(t + h) - fn(t - h)) / (2 * h)


def around(c, cx, cy, sx=1, sy=1, rot=0, dx=0, dy=0):
    c.translate(cx + dx, cy + dy)
    c.rotate(rot)
    c.scale(sx, sy)
    c.translate(-cx, -cy)


def layer(c, a=1.0, blur=0.0):
    """Opens a layer with alpha and an optional blur; close it with c.restore()."""
    p = skia.Paint(Alphaf=max(0.0, min(1.0, a)))
    if blur > .3:
        p.setImageFilter(skia.ImageFilters.Blur(blur, blur))
    c.saveLayer(None, p)


def rise(c, t, t0, cx, cy, draw, dy=80, w=13, z=.5, s0=.86, blur=18):
    """The house entrance: slides up and scales in on a spring while it comes into focus."""
    dt = t - t0
    if dt <= 0:
        return
    p = spring(dt, w, z)
    s = s0 + (1 - s0) * p
    c.save()
    around(c, cx, cy, s, s, dy=(1 - p) * dy)
    sig = blur * max(0, 1 - dt / .3)
    a = min(1, dt / .16)
    if sig > .3 or a < 1:
        layer(c, a, sig)
        draw()
        c.restore()
    else:
        draw()
    c.restore()


def pop(c, t, t0, cx, cy, draw, w=17.0, z=.38):
    """Small things (dots, icons, values): overshoot with a little squash."""
    dt = t - t0
    if dt <= 0:
        return
    s = spring(dt, w, z)
    v = max(-1.2, min(1.2, d(lambda u: spring(u, w, z), dt) / w))
    c.save()
    around(c, cx, cy, max(s * (1 + v * .22), .001), max(s * (1 - v * .22), .001))
    draw()
    c.restore()


def fade_out(c, t, t1, cx, cy, draw, dur=.22):
    """Exit: shrinks a touch, drifts up and blurs away from t1."""
    u = (t - t1) / dur
    if u >= 1:
        return
    if u <= 0:
        draw()
        return
    c.save()
    around(c, cx, cy, 1 - .08 * u, 1 - .08 * u, dy=-30 * u)
    layer(c, 1 - u, 14 * u)
    draw()
    c.restore()
    c.restore()


def pulse(t, t0, a=.12, w=16, k=6):
    dt = t - t0
    return 1.0 if dt <= 0 else 1 + a * math.exp(-k * dt) * math.sin(w * dt)


def ripple(c, x, y, t, t0, color=WHITE, r0=40, r1=260, a=.7):
    dt = t - t0
    if not 0 < dt < .7:
        return
    for k in (0, .12):
        u = (dt - k) / (.7 - k)
        if 0 < u < 1:
            e = 1 - (1 - u) ** 3
            c.drawCircle(x, y, r0 + (r1 - r0) * e, stroke(color, 6 * (1 - u), a * (1 - u)))


def slide(t, t0, w=12, z=.6):
    """Spring progress 0..1 for moving a selection ring or any value between two states."""
    return spring(t - t0, w, z) if t > t0 else 0.0


# ------------------------------------------------------------------ presenter: live video; each slot has its own corner radius and crop
# (x, y, w, h, radius, crop) in reference space. crop 0 = whole frame, 1 = face crop, above 1 = tighter on the face.
SLOTS = dict(hero=(290, 420, 500, 640, 72, 1), center=(240, 300, 600, 800, 72, .55),
             avatar=(66, 84, 172, 172, 86, 1.25), avatar_r=(842, 84, 172, 172, 86, 1.25),
             tl=(66, 66, 300, 400, 56, 1), tr=(714, 66, 300, 400, 56, 1), bl=(66, 974, 300, 400, 56, 1),
             br=(714, 974, 300, 400, 56, 1), left=(66, 420, 420, 560, 64, 1), right=(594, 420, 420, 560, 64, 1))


def resolve_slot(slot, fit):
    if slot == "full":
        return (0.0, 0.0, fit.lay.W, fit.lay.H, 0.0, 0.0)
    x, y, w, h, *rest = SLOTS[slot] if isinstance(slot, str) else slot
    r = rest[0] if rest else min(w, h) * .18
    m = rest[1] if len(rest) > 1 else 1.0
    s = fit.s
    return (fit.ox + x * s, fit.oy + y * s, w * s, h * s, r * s, m)


def presenter_state(t, keys, fit):
    """Springs between keyed slots. Returns (x, y, w, h, r, m, visible) in frame units."""
    cur, vis, prev = None, 1.0, None
    for tk, slot in keys:
        if t < tk:
            break
        if cur is None:
            cur = resolve_slot("full" if slot == "hidden" else slot, fit)
            vis = 0.0 if slot == "hidden" else 1.0
            prev = slot
            continue
        k = spring(t - tk, 10, .62)
        if slot == "hidden":
            vis *= 1 - min(1.0, (t - tk) / .2) ** 2
        else:
            to = resolve_slot(slot, fit)
            if prev == "hidden":
                cur, vis = to, k
            else:
                cur = tuple(a + (b - a) * k for a, b in zip(cur, to))
        prev = slot
    if cur is None:
        cur = resolve_slot("full", fit)
    return (*cur, vis)


def draw_presenter(c, state, img, crop, scale, lay):
    """crop is the face rectangle in design units. The source rect eases from the whole frame to the face at the
    slot's aspect, so the face never distorts; round slots crop tighter."""
    x, y, w, h, r, m, vis = state
    if vis <= .003 or img is None or w < 2 or h < 2:
        return
    asp = w / h
    full = (lay.W, lay.W / asp) if asp >= lay.W / lay.H else (lay.H * asp, lay.H)
    z = 1 / max(m, 1)
    fw, fh = crop.width(), crop.height()
    face = (fw * z, fw * z / asp) if asp >= fw / fh else (fh * z * asp, fh * z)
    mm = max(0.0, min(m, 1.0))
    sw, sh = full[0] + (face[0] - full[0]) * mm, full[1] + (face[1] - full[1]) * mm
    cx = lay.W / 2 + (crop.centerX() - lay.W / 2) * mm
    cy = lay.H / 2 + (crop.top() + fh * .44 - lay.H / 2) * mm
    cx = min(max(cx, sw / 2), lay.W - sw / 2)
    cy = min(max(cy, sh / 2), lay.H - sh / 2)
    src = skia.Rect.MakeXYWH((cx - sw / 2) * scale, (cy - sh / 2) * scale, sw * scale, sh * scale)
    c.save()
    c.translate(x + w / 2, y + h / 2)
    c.scale(vis, vis)
    c.translate(-w / 2, -h / 2)
    edge = min(1.0, r / 30)
    if edge > .01:
        c.drawRRect(rrect(20 * edge, 26 * edge, w - 40 * edge, h, r), fill("#4A4FA0", .16 * edge, 30 * edge))
    c.save()
    c.clipRRect(rrect(0, 0, w, h, r), doAntiAlias=True)
    c.drawImageRect(img, src, skia.Rect.MakeWH(w, h), skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear),
                    None, skia.Canvas.kFast_SrcRectConstraint)
    c.restore()
    if edge > .01:
        c.drawRRect(rrect(2, 2, w - 4, h - 4, max(0, r - 2)), stroke(WHITE, 4, .8 * edge))
    c.restore()


# ------------------------------------------------------------------ captions
def caption_line(t):
    for i, ln in enumerate(CAPTIONS):
        nxt = CAPTIONS[i + 1]["t0"] if i + 1 < len(CAPTIONS) else ln["t1"] + 1.0
        if ln["t0"] - .05 <= t < min(nxt, ln["t1"] + .6):
            return ln
    return None


def draw_captions(c, t, lay):
    """Flat white pill anchored to the real frame; the active character turns accent violet."""
    ln = caption_line(t)
    if not ln:
        return
    chars, active = [], -1
    for u in ln["highlight"]["units"]:
        for ch in u["text"]:
            if ch in "，。、？！：；,.!?;:":
                continue
            if u["start"] <= t < u["end"] and active < 0:
                active = len(chars)
            chars.append(ch)
    s = "".join(chars)
    size = 40
    maxw = lay.W - 120
    w = text_w(s, size, "m", 0) + 80
    if w > maxw:
        size *= maxw / w
        w = maxw
    y = lay.H - 76
    x = (lay.W - w) / 2
    hgt = size * 1.9

    def draw():
        c.drawRRect(rrect(x + 10, y - size * 1.0, w - 20, hgt, hgt / 2), fill("#5A5FB0", .08, 16))
        c.drawRRect(rrect(x, y - size * 1.3, w, hgt, hgt / 2), fill(WHITE))
        px = x + 40 * size / 40
        for i, ch in enumerate(s):
            px += text(c, ch, px, y, size, ACCENT if i == active else NAVY, "l", "m", 0)
    rise(c, t, ln["t0"] - .05, lay.W / 2, y - size * .35, draw, dy=24, w=18, z=.6, s0=.94, blur=8)


# ------------------------------------------------------------------ frame
class Fit:
    """Maps the 1080x1440 reference space into the real frame (uniform scale, centred)."""
    def __init__(self, lay):
        self.lay = lay
        self.s = min(lay.W / W, lay.H / H)
        self.ox, self.oy = (lay.W - W * self.s) / 2, (lay.H - H * self.s) / 2

    def enter(self, c):
        c.translate(self.ox, self.oy)
        c.scale(self.s, self.s)


_FIT = {}


def fit_for(lay):
    return _FIT.setdefault(id(lay), Fit(lay))


def _active(scenes, t, layer_):
    return [s for s in scenes if s.get("layer", "stage") == layer_ and s["t0"] <= t < s["t1"]]


def _cuts(scenes):
    """Scene-change times that frost: the start and end of every stage scene unless it says enter=None."""
    out = set()
    for s in scenes:
        if s.get("layer", "stage") == "stage" and s.get("enter", "frost") == "frost":
            out.update((round(s["t0"], 4), round(s["t1"], 4)))
    return sorted(out)


def transition(t, cuts):
    """(blur, scale, cover): frost over the last FROST seconds before a cut, focus-pull in for FOCUS after it."""
    blur, s, cover = 0.0, 1.0, 0.0
    for b in cuts:
        if b - FROST <= t < b:
            u = max(0.0, 1 - (b - t) / FROST)       # float error can dip a hair below 0, and u ** 1.5 would go complex
            blur, s, cover = max(blur, 30 * u * u), 1 + .04 * u, u ** 1.5
        elif b <= t < b + FOCUS and b > 0:
            since = t - b
            blur = max(blur, 26 * max(0.0, 1 - since / .4))
            s = 1.05 - .05 * spring(since, 11, .7)
    return blur, s, cover


def render_frame(c, P, t, img, scale):
    """SCENES: dict(t0, t1, fn, layer="stage"|"over", enter="frost"|None).
    stage scenes sit under the presenter on the lavender ground, over scenes above the presenter. Between scenes the
    presenter's slot decides the look; with no stage scene the ground still shows around a non-full presenter."""
    lay = P.layout
    fit = fit_for(lay)
    if not hasattr(P, "_sg_cuts"):
        P._sg_cuts = _cuts(P.SCENES)
    blur, s, cover = transition(t, P._sg_cuts)
    c.save()
    c.scale(scale, scale)
    wrap = blur > .3 or abs(s - 1) > 1e-4
    if wrap:
        c.save()
        around(c, lay.W / 2, lay.H / 2, s, s)
        layer(c, 1, blur)
    background(c, lay.W, lay.H)
    c.save()
    fit.enter(c)
    for sc in _active(P.SCENES, t, "stage"):
        sc["fn"](c, t)
    c.restore()
    state = presenter_state(t, P.presenter, fit)
    draw_presenter(c, state, img, P.crop, scale, lay)
    full = max(0.0, min(1.0, (state[2] / lay.W - .6) / .4)) * state[6]      # fades as the video leaves full frame
    if full > .01:
        c.drawRect(skia.Rect.MakeWH(lay.W, lay.H), lin(0, lay.H * .43, 0, lay.H * .83, [(NAVY, 0), (NAVY, .62 * full)]))
    c.save()
    fit.enter(c)
    for sc in _active(P.SCENES, t, "over"):
        sc["fn"](c, t)
    c.restore()
    if wrap:
        c.restore()
        c.restore()
    if cover > .001:
        layer(c, cover)
        background(c, lay.W, lay.H)
        c.restore()
    if P.captions_on and not any(a <= t < b for a, b in P.caption_mute) and cover < .5:
        draw_captions(c, t, lay)
    c.restore()
