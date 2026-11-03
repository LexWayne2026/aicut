"""wbx.popcard: Template 2 "Pop Card". White cards, loud colour, inked cartoon objects, bouncy motion graphics.

Scenes are authored in a 1080x1440 reference space that is uniformly fitted into the real frame, while backgrounds
bleed to the frame edges. The presenter is live video in any slot (see PRESENTER in references/template-2-popcard.md).
Every function is a pure function of time t. Template 1 does not import this module.
"""
import math
from pathlib import Path

import skia

from wbx.core import load_typeface
from wbx.cues import CAPTIONS

ROOT = Path(__file__).resolve().parent.parent
W, H = 1080, 1440                    # reference space

INK = "#111114"
WHITE = "#FFFFFF"
LIME = "#7BE800"
PINK = "#FF5C93"
YELLOW = "#FFE500"
BLUE = "#2EB6FF"
VIOLET = "#7C3AED"
ORANGE = "#FF9F1C"
MUTE = "#6E6E78"
SOFT = "#F2F2F5"
LW = 7                               # outline width of the cartoon objects
SLAM = 0.34                          # seconds a colour sheet takes to cover the frame


# ------------------------------------------------------------------ fonts
FONT_FILES = dict(zh_heavy="ResourceHanRoundedCN-Heavy.ttf", zh_body="ResourceHanRoundedCN-Medium.ttf",
                  la_heavy="Outfit-ExtraBold.ttf", la_body="Outfit-Medium.ttf")
_TF = {}


def tf(key):
    if key not in _TF:
        _TF[key] = load_typeface(ROOT / "fonts" / FONT_FILES[key])
    return _TF[key]


def fonts(size, heavy=True):
    zh = skia.Font(tf("zh_heavy" if heavy else "zh_body"), size)
    la = skia.Font(tf("la_heavy" if heavy else "la_body"), size * 1.02)
    for f in (zh, la):
        f.setSubpixel(True)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        f.setHinting(skia.FontHinting.kNone)
    return zh, la


# ------------------------------------------------------------------ drawing primitives and cartoon objects
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


def text_w(s, size, heavy=True, track=-0.015):
    zh, la = fonts(size, heavy)
    return sum((la if ord(ch) < 0x2E80 else zh).measureText(ch) + size * track for ch in s)


def text(c, s, x, y, size, color=INK, align="l", heavy=True, track=-0.015, a=1.0):
    """Chinese in Resource Han Rounded, Latin and numerals in Outfit, per character."""
    zh, la = fonts(size, heavy)
    w = text_w(s, size, heavy, track)
    x -= {"l": 0, "c": w / 2, "r": w}[align]
    fp = fill(color, a)
    for ch in s:
        f = la if ord(ch) < 0x2E80 else zh
        c.drawString(ch, x, y, f, fp)
        x += f.measureText(ch) + size * track
    return w


def pill(c, x, cy, s, size, bg=INK, fg=WHITE, align="l", padx=None, pady=None, rot=0, shadow=None):
    padx = size * 0.62 if padx is None else padx
    pady = size * 0.36 if pady is None else pady
    w = text_w(s, size) + padx * 2
    h = size + pady * 2
    left = x - {"l": 0, "c": w / 2, "r": w}[align]
    c.save()
    c.translate(left + w / 2, cy)
    c.rotate(rot)
    r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), h / 2, h / 2)
    if shadow:
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -h / 2 + 10, w, h), h / 2, h / 2), fill(shadow, .32, 14))
    c.drawRRect(r, fill(bg))
    text(c, s, 0, size * 0.355, size, fg, "c")
    c.restore()
    return w


def card(c, x, y, w, h, r=48, rot=0, bg=WHITE, shadow=INK, sa=.18):
    c.save()
    c.translate(x + w / 2, y + h / 2)
    c.rotate(rot)
    c.translate(-w / 2, -h / 2)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(0, 18, w, h), r, r), fill(shadow, sa, 26))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeWH(w, h), r, r), fill(bg))
    return lambda: c.restore()


def rr(x, y, w, h, r):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r))
    return p


def shape(c, p, color, lw=LW):
    c.drawPath(p, fill(color))
    c.drawPath(p, stroke(INK, lw))


def bottle(c, cx, cy, s, body, label, rot=0, sticker=False, cap=INK):
    c.save()
    c.translate(cx, cy)
    c.rotate(rot)
    c.scale(s, s)
    parts = [rr(-58, -82, 116, 192, 30), rr(-42, -122, 84, 46, 14)]
    if sticker:
        for p in parts:
            c.drawPath(p, stroke(WHITE, 34))
    shape(c, parts[0], body)
    shape(c, parts[1], cap)
    for i in (-22, 0, 22):
        c.drawLine(i, -112, i, -86, stroke(WHITE, 4, .55))
    shape(c, rr(-58, -32, 116, 86, 0), WHITE)
    text(c, label, 0, 26, 42 if len(label) <= 2 else 36, INK, "c")
    c.drawLine(-38, -62, -38, -46, stroke(WHITE, 8, .8))
    c.restore()


def tablet(c, cx, cy, r, color=WHITE, rot=-18, score=True):
    c.save()
    c.translate(cx, cy)
    c.rotate(rot)
    c.drawCircle(4, 8, r, fill(INK))
    c.drawCircle(0, 0, r, fill(color))
    c.drawCircle(0, 0, r, stroke(INK, LW))
    if score:
        c.drawLine(-r * .62, 0, r * .62, 0, stroke(INK, LW * .7))
    c.restore()


def capsule(c, cx, cy, s, a, b, rot=-35, dots=False):
    c.save()
    c.translate(cx, cy)
    c.rotate(rot)
    c.scale(s, s)
    body = rr(-90, -38, 180, 76, 38)
    c.save()
    c.clipPath(body, doAntiAlias=True)
    c.drawRect(skia.Rect.MakeLTRB(-90, -40, 0, 40), fill(a))
    c.drawRect(skia.Rect.MakeLTRB(0, -40, 90, 40), fill(b))
    if dots:
        for dx, dy in [(14, -12), (38, 10), (60, -14), (30, -20), (58, 14)]:
            c.drawCircle(dx, dy, 7, fill(a))
    c.restore()
    c.drawPath(body, stroke(INK, LW))
    c.drawLine(0, -38, 0, 38, stroke(INK, LW))
    c.drawLine(-66, -18, -36, -18, stroke(WHITE, 7, .85))
    c.restore()


def coated(c, cx, cy, s):
    c.save()
    c.translate(cx, cy)
    c.rotate(-16)
    c.scale(s, s)
    c.drawOval(skia.Rect.MakeLTRB(-88, -62, 88, 62), fill(BLUE))
    c.drawOval(skia.Rect.MakeLTRB(-88, -62, 88, 62), stroke(INK, LW))
    c.drawOval(skia.Rect.MakeLTRB(-60, -38, 60, 38), fill(WHITE))
    c.drawOval(skia.Rect.MakeLTRB(-60, -38, 60, 38), stroke(INK, LW * .7))
    c.restore()


def liposome(c, cx, cy, s):
    c.save()
    c.translate(cx, cy)
    c.scale(s, s)
    n = 18
    c.drawCircle(0, 0, 66, fill("#FFD8E6"))
    for i in range(n):
        a = i / n * math.tau
        c.drawCircle(84 * math.cos(a), 84 * math.sin(a), 13, fill(ORANGE))
        c.drawCircle(84 * math.cos(a), 84 * math.sin(a), 13, stroke(INK, 5))
    c.drawCircle(0, 0, 66, stroke(INK, LW))
    c.drawCircle(-12, 8, 22, fill(PINK))
    c.drawCircle(-12, 8, 22, stroke(INK, 5))
    c.drawCircle(24, -22, 12, fill(VIOLET))
    c.drawCircle(24, -22, 12, stroke(INK, 5))
    c.restore()


def gummy(c, cx, cy, s, color=PINK):
    c.save()
    c.translate(cx, cy)
    c.rotate(8)
    c.scale(s, s)
    q = skia.Path()
    for x, y, r in [(-36, -78, 22), (36, -78, 22), (0, -50, 52), (0, 44, 62), (-54, 8, 22), (54, 8, 22), (-40, 96, 26), (40, 96, 26)]:
        p = skia.Path()
        p.addCircle(x, y, r)
        q = skia.Op(q, p, skia.PathOp.kUnion_PathOp)
    shape(c, q, color)
    c.drawCircle(-18, -58, 6.5, fill(INK))
    c.drawCircle(18, -58, 6.5, fill(INK))
    c.drawLine(-28, 16, -10, 2, stroke(WHITE, 8, .8))
    c.restore()


def dropper(c, cx, cy, s):
    c.save()
    c.translate(cx, cy)
    c.rotate(10)
    c.scale(s, s)
    shape(c, rr(-20, -130, 40, 56, 18), INK)
    shape(c, rr(-30, -82, 60, 34, 8), WHITE)
    body = rr(-62, -54, 124, 176, 32)
    c.save()
    c.clipPath(body, doAntiAlias=True)
    c.drawRect(skia.Rect.MakeLTRB(-70, -60, 70, 130), fill("#BFEFFF"))
    c.drawRect(skia.Rect.MakeLTRB(-70, 4, 70, 130), fill(BLUE))
    c.restore()
    c.drawPath(body, stroke(INK, LW))
    c.drawLine(-62, 4, 62, 4, stroke(INK, 5))
    c.drawCircle(-20, 48, 8, fill(WHITE))
    c.drawCircle(14, 80, 6, fill(WHITE))
    c.restore()


def star(c, cx, cy, r, color=WHITE):
    p = skia.Path()
    p.moveTo(cx, cy - r)
    for dx, dy in [(r, 0), (0, r), (-r, 0), (0, -r)]:
        p.quadTo(cx, cy, cx + dx, cy + dy)
    c.drawPath(p, fill(color))


def badge(c, cx, cy, s, n=None):
    """The black squircle that carries the step number, echoing the reference's app mark."""
    c.save()
    c.translate(cx, cy)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-s / 2, -s / 2 + 12, s, s), s * .28, s * .28), fill(INK, .3, 16))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-s / 2, -s / 2, s, s), s * .28, s * .28), fill(INK))
    if n:
        text(c, n, 0, s * .22, s * .62, WHITE, "c")
    else:
        star(c, 0, 0, s * .32)
    c.restore()


def rays(c, cx, cy, color, n=18):
    for i in range(n):
        a0 = i / n * math.tau
        a1 = a0 + math.tau / n / 2
        p = skia.Path()
        p.moveTo(cx, cy)
        p.lineTo(cx + 4200 * math.cos(a0), cy + 4200 * math.sin(a0))
        p.lineTo(cx + 4200 * math.cos(a1), cy + 4200 * math.sin(a1))
        p.close()
        c.drawPath(p, fill(color))


def leaf(c, cx, cy, s):
    c.save()
    c.translate(cx, cy)
    c.rotate(35)
    c.scale(s, s)
    p = skia.Path()
    p.moveTo(0, -70)
    p.quadTo(62, -10, 0, 70)
    p.quadTo(-62, -10, 0, -70)
    shape(c, p, LIME)
    c.drawLine(0, -36, 0, 52, stroke(INK, 6))
    c.restore()


def globe(c, cx, cy, s):
    c.save()
    c.translate(cx, cy)
    c.scale(s, s)
    c.drawCircle(0, 0, 66, fill(BLUE))
    c.drawCircle(0, 0, 66, stroke(INK, LW))
    c.drawOval(skia.Rect.MakeLTRB(-28, -66, 28, 66), stroke(INK, 5))
    c.drawLine(-66, 0, 66, 0, stroke(INK, 5))
    c.restore()


# ------------------------------------------------------------------ motion
def spring(t, w=17.0, z=.36):
    if t <= 0:
        return 0.0
    wd = w * math.sqrt(1 - z * z)
    return 1 - math.exp(-z * w * t) * (math.cos(wd * t) + z * w / wd * math.sin(wd * t))


def anticip(t):
    if t < .10:
        return -.07 * math.sin(t / .10 * math.pi)
    return spring(t - .10, 15, .42)


def drop(t):
    """Falls with gravity, then each bounce is shorter (0 = top, 1 = rest)."""
    g, a = .30, 0.0
    if t < g:
        return (t / g) ** 2
    t -= g
    for d, h in [(.26, .22), (.15, .07), (.08, .02)]:
        if t < d:
            u = t / d
            return 1 - 4 * h * u * (1 - u)
        t -= d
    return 1.0


def m_drop(t):
    y = drop(t)
    hit = sum(math.exp(-((t - k) / .025) ** 2) * a for k, a in [(.30, .34), (.56, .16), (.71, .07)])
    return dict(dy=(y - 1) * 105, sx=1 + hit, sy=1 - hit * .8)


def around(c, cx, cy, sx=1, sy=1, rot=0, dx=0, dy=0):
    c.translate(cx + dx, cy + dy)
    c.rotate(rot)
    c.scale(sx, sy)
    c.translate(-cx, -cy)


def d(fn, t, h=.004):
    return (fn(t + h) - fn(t - h)) / (2 * h)


def pop(c, t, t0, cx, cy, draw, w=17.0, z=.36, spin=0):
    dt = t - t0
    if dt <= 0:
        return
    s = spring(dt, w, z)
    v = max(-1.2, min(1.2, d(lambda u: spring(u, w, z), dt) / w))
    c.save()
    around(c, cx, cy, max(s * (1 + v * .3), .001), max(s * (1 - v * .3), .001), rot=(1 - s) * spin)
    draw()
    c.restore()


def whip(c, t, t0, cx, cy, draw, dist=420, sign=-1, spin=16):
    dt = t - t0
    if dt <= 0:
        return
    p = anticip(dt)
    if dt < .10:
        p = 0                                # hold off screen during the pull back; only the fling is visible
    speed = min(abs(d(anticip, dt)) / 40, .28)
    c.save()
    around(c, cx, cy, 1 + speed, 1 - speed * .55, rot=(1 - p) * spin * -sign, dx=(1 - p) * dist * sign)
    draw()
    c.restore()


def back_out(c, t, t1, cx, cy, draw, dur=.2):
    """Grows a touch, then shrinks away."""
    u = (t - t1) / dur
    if u >= 1:
        return
    s = 1.0 if u <= 0 else (1 + .18 * math.sin(u * math.pi)) * (1 - u ** 3)
    c.save()
    around(c, cx, cy, s, s)
    draw()
    c.restore()


def drop_text(c, s, x, y, size, color, t, t0, stag=.04, align="l", fall=None, track=-.015):
    x -= {"l": 0, "c": text_w(s, size, track=track) / 2}[align]
    fall = fall or size * 1.5
    for i, ch in enumerate(s):
        adv = text_w(ch, size, track=track)
        dt = t - t0 - i * stag
        if dt > 0:
            v = m_drop(dt)
            c.save()
            around(c, x + adv / 2, y, v["sx"], v["sy"], dy=(drop(dt) - 1) * fall)
            text(c, ch, x, y, size, color, track=track)
            c.restore()
        x += adv


def pulse(t, t0, a=.2, w=16, k=5):
    dt = t - t0
    return 1.0 if dt <= 0 else 1 + a * math.exp(-k * dt) * math.sin(w * dt)


def idle(t, seed=0, amp=5):
    return amp * math.sin(2.1 * t + seed * 1.7), amp * .28 * math.sin(1.6 * t + seed)


def burst(c, x, y, t, t0, color, r0=70, r1=240, n=10, seed=0):
    dt = t - t0
    if not 0 < dt < .6:
        return
    p = 1 - (1 - dt / .6) ** 3
    for i in range(n):
        a = i / n * math.tau + seed
        r = r0 + (r1 - r0) * p * (.75 + .25 * math.sin(i * 7.3))
        star(c, x + r * math.cos(a), y + r * math.sin(a), 24 * (1 - dt / .6), color) if i % 2 else \
            c.drawCircle(x + r * math.cos(a), y + r * math.sin(a), 12 * (1 - dt / .6), fill(color))


def dome(c, y, color=WHITE, bulge=120, w=W):
    """Curved colour sheet; bleeds far past the reference frame so it also fills wider or taller outputs."""
    p = skia.Path()
    p.moveTo(-4000, y + bulge)
    p.lineTo(0, y + bulge)
    p.quadTo(w / 2, y - bulge, w, y + bulge)
    p.lineTo(w + 4000, y + bulge)
    p.lineTo(w + 4000, 6000)
    p.lineTo(-4000, 6000)
    p.close()
    c.drawPath(p, fill(color))


# ------------------------------------------------------------------ presenter: live video in any slot
SLOTS = dict(tl=(66, 60, 270, 360, -3), tr=(746, 66, 270, 360, 3), bl=(66, 1010, 210, 280, -3), br=(804, 1010, 210, 280, 3),
             center=(270, 400, 540, 720, -1.5), left=(66, 500, 360, 480, -2), right=(654, 500, 360, 480, 2))


def resolve_slot(slot, fit):
    """A slot is "full", a SLOTS name, or (x, y, w, h[, rot]) in reference space. Returns frame rect + rotation."""
    if slot == "full":
        return (0.0, 0.0, float(fit.lay.W), float(fit.lay.H), 0.0)
    x, y, w, h, *rot = SLOTS[slot] if isinstance(slot, str) else slot
    return (fit.ox + x * fit.s, fit.oy + y * fit.s, w * fit.s, h * fit.s, rot[0] if rot else 0.0)


def presenter_state(t, keys, fit):
    """Springs between keyed slots with an arc and overshoot. Returns (x, y, w, h, rot, m, visible);
    m = 0 full frame .. 1 tile. "hidden" pops the tile away and back."""
    cur, vis, arc, prev = None, 1.0, 0.0, None
    for tk, slot in keys:
        if t < tk:
            break
        if cur is None:
            cur = resolve_slot("full" if slot == "hidden" else slot, fit)
            vis = 0.0 if slot == "hidden" else 1.0
            prev = slot
            continue
        k = spring(t - tk, 10, .52)
        if slot == "hidden":
            vis *= 1 - min(1.0, (t - tk) / .18) ** 2
        else:
            to = resolve_slot(slot, fit)
            if prev == "hidden":
                cur, vis = to, k
            else:
                arc = -70 * fit.s * math.sin(math.pi * min(k, 1)) if prev != "full" and slot != "full" else 0.0
                cur = tuple(a + (b - a) * k for a, b in zip(cur, to))
        prev = slot
    if cur is None:
        cur = resolve_slot("full", fit)
    x, y, w, h, rot = cur
    span = max(1.0, fit.lay.W - fit.tile_w)
    m = max(0.0, min(1.0, 1 - (w - fit.tile_w) / span))
    return x, y + arc, w, h, rot, m, vis


def draw_presenter(c, state, img, crop, scale, lay):
    """crop is the face rectangle in design units. Source rect eases from the whole frame to the face, keeping
    the source aspect, so the face never distorts whatever the slot's size."""
    x, y, w, h, rot, m, vis = state
    if vis <= .003 or img is None:
        return
    sx, sy = crop.left() * m, crop.top() * m
    sw, sh = lay.W + (crop.width() - lay.W) * m, lay.H + (crop.height() - lay.H) * m
    aspect = w / h
    if sw / sh > aspect:                 # fit a non-matching slot by trimming the crop, not stretching it
        nw = sh * aspect
        sx, sw = sx + (sw - nw) / 2, nw
    else:
        nh = sw / aspect
        sy, sh = sy + (sh - nh) / 2, nh
    src = skia.Rect.MakeXYWH(sx * scale, sy * scale, sw * scale, sh * scale)
    full = w >= lay.W - 2
    r = 0 if full else 50 * m * min(1.0, w / 270)
    edge = 0 if full else min(1.0, m * 3)
    c.save()
    c.translate(x + w / 2, y + h / 2)
    c.rotate(rot)
    c.scale(vis, vis)
    c.translate(-w / 2, -h / 2)
    if edge > .01:
        b = 10 * edge
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-b, 8, w + 2 * b, h + 2 * b), r + b, r + b), fill(INK, .28 * edge, 22))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-b, -b, w + 2 * b, h + 2 * b), r + b, r + b), fill(WHITE, edge))
    c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeWH(w, h), r, r), doAntiAlias=True)
    c.drawImageRect(img, src, skia.Rect.MakeWH(w, h), skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear),
                    None, skia.Canvas.kFast_SrcRectConstraint)
    c.restore()


# ------------------------------------------------------------------ captions
def caption_line(t):
    for i, ln in enumerate(CAPTIONS):
        nxt = CAPTIONS[i + 1]["t0"] if i + 1 < len(CAPTIONS) else ln["t1"] + 1.0
        if ln["t0"] - .05 <= t < min(nxt, ln["t1"] + .6):
            return ln
    return None


def draw_captions(c, t, lay, on_light=False):
    """Pill caption anchored to the real frame; the active character lights up."""
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
    w = text_w(s, size, track=0) + 72
    if w > maxw:
        size *= maxw / w
        w = maxw
    y = lay.H - 78
    x = (lay.W - w) / 2

    def draw():
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y - size * 1.25, w, size * 1.75), size * .875, size * .875), fill(INK))
        px = x + 36 * size / 40
        for i, ch in enumerate(s):
            px += text(c, ch, px, y, size, LIME if i == active else WHITE, track=0)
    pop(c, t, ln["t0"] - .05, lay.W / 2, y - size * .4, draw, w=24, z=.5)


# ------------------------------------------------------------------ frame
class Fit:
    """Maps the 1080x1440 reference space into the real frame (uniform scale, centred)."""
    def __init__(self, lay):
        self.lay = lay
        self.s = min(lay.W / W, lay.H / H)
        self.ox, self.oy = (lay.W - W * self.s) / 2, (lay.H - H * self.s) / 2
        self.tile_w = 270 * self.s

    def enter(self, c):
        c.translate(self.ox, self.oy)
        c.scale(self.s, self.s)


_FIT = {}


def fit_for(lay):
    return _FIT.setdefault(id(lay), Fit(lay))


def _active(scenes, t, layer):
    return [s for s in scenes if s.get("layer", "stage") == layer and s["t0"] <= t < s["t1"]]


def render_frame(c, P, t, img, scale):
    """SCENES: dict(t0, t1, fn, bg=colour, layer="stage"|"over", enter="slam"|None).
    stage scenes sit under the presenter, over scenes above it. Between scenes the presenter's slot decides the look."""
    lay = P.layout
    fit = fit_for(lay)
    c.save()
    c.scale(scale, scale)
    stage = _active(P.SCENES, t, "stage")
    c.drawPaint(fill(stage[-1].get("bg", WHITE) if stage else WHITE))
    shake = 0.0
    for s in stage:
        since = t - s["t0"]
        if s.get("enter") == "slam" and since < .9:
            shake = -46 * math.exp(-7 * since) * math.cos(19 * since)
    c.save()
    fit.enter(c)
    c.translate(0, shake)
    for s in stage:
        s["fn"](c, t)
    c.restore()
    state = presenter_state(t, P.presenter, fit)
    draw_presenter(c, state, img, P.crop, scale, lay)
    full = (1 - state[5]) * state[6]
    if full > .01:
        g = skia.Paint(Shader=skia.GradientShader.MakeLinear(
            [skia.Point(0, lay.H * .53), skia.Point(0, lay.H * .82)], [col(INK, 0), col(INK, .86 * full)]))
        c.drawRect(skia.Rect.MakeWH(lay.W, lay.H), g)
    c.save()
    fit.enter(c)
    for s in _active(P.SCENES, t, "over"):
        s["fn"](c, t)
    c.restore()
    for s in P.SCENES:                     # the colour sheet rises over everything just before a slam scene starts
        if s.get("enter") == "slam" and s["t0"] - SLAM <= t < s["t0"]:
            p = 1 - (s["t0"] - t) / SLAM
            y = lambda u: lay.H + 160 - (lay.H + 340) * u ** 2.2  # noqa: E731
            dome(c, y(min(1, p * 1.12)), s.get("slam2", VIOLET), 140, lay.W)
            if p > .25:
                dome(c, y((p - .25) / .75), s.get("bg", WHITE), 140, lay.W)
    if P.captions_on and not any(a <= t < b for a, b in P.caption_mute):
        draw_captions(c, t, lay)
    c.restore()
