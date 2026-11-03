"""wbx.core — the "grid whiteboard + pencil" style engine.

Everything is drawn in a fixed 1080x1440 design space; the renderer scales the
canvas for previews. Every function is a pure function of time t (deterministic).
Pencil look: strokes are jittered with a seeded DiscretePathEffect and drawn in two
passes; fills are pencil hatching; emphasis uses a translucent marker swash.
"""
import math
from contextlib import contextmanager
from pathlib import Path

import skia

ROOT = Path(__file__).resolve().parent.parent      # skill / render-kit root (fonts/, music/ live here)
W, H = 1080, 1440   # authoring space for stage content (see wbx.layout); real frames adapt to the source


# ---------------------------------------------------------------- palette
def hexc(h, a=1.0):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return skia.Color(r, g, b, max(0, min(255, int(round(a * 255)))))


PAPER = "#F8F7F2"    # whiteboard / paper
BG = PAPER
GRID = "#8FAACB"     # blue-grey grid lines
INK = "#26262B"      # graphite
MUTE = "#85858C"     # light pencil
DIM = "#C9C9CE"
BLUE = "#2B6CD9"     # blue pencil — accent
GREEN = "#1E9A55"    # OTC / drug
AMBER = "#E07B16"    # imported / supplement
RED = "#E0403A"      # not-equal / warning
CYAN = "#0E8F9C"     # teal pencil
MARKER = "#FFD84D"   # highlighter


# ---------------------------------------------------------------- time
def clamp01(x):
    return 0.0 if x <= 0 else 1.0 if x >= 1 else x


def lerp(a, b, p):
    return a + (b - a) * p


def soft(dt, w=9.0):
    """Critically damped (no overshoot)."""
    if dt <= 0:
        return 0.0
    return 1 - math.exp(-w * dt) * (1 + w * dt)


def spring(dt, w=11.0, z=0.80):
    """Damped spring step response, dt in seconds. Slight overshoot, settles ~0.6s."""
    if dt <= 0:
        return 0.0
    if dt > 3.0:
        return 1.0
    if z >= 0.999:
        return soft(dt, w)
    wd = w * math.sqrt(1 - z * z)
    return 1 - math.exp(-z * w * dt) * (math.cos(wd * dt) + (z * w / wd) * math.sin(wd * dt))


def ease_out(p):
    p = clamp01(p)
    return 1 - (1 - p) ** 4


def ease_io(p):
    p = clamp01(p)
    return p * p * (3 - 2 * p) if p < 1 else 1.0


def expo_io(p):
    p = clamp01(p)
    if p in (0.0, 1.0):
        return p
    return 2 ** (20 * p - 10) / 2 if p < 0.5 else (2 - 2 ** (-20 * p + 10)) / 2


def out_env(t, t1, dur=0.38):
    """1 before t1, eased to 0 over dur after t1."""
    if t1 is None:
        return 1.0
    return 1 - ease_out((t - t1) / dur)


# ---------------------------------------------------------------- Remotion-style timing toolkit
# interpolate() over explicit keyframes with per-segment easing, clamped by default; a bezier ease that
# matches CSS cubic-bezier(); a no-bounce "push" spring; perceptual (geometric) scale; posterize.
def bezier(x1, y1, x2, y2):
    """CSS-style cubic-bezier easing function."""
    def sample(a1, a2, u):
        return ((1 - 3 * a2 + 3 * a1) * u + (3 * a2 - 6 * a1)) * u * u + 3 * a1 * u

    def f(x):
        x = clamp01(x)
        if x in (0.0, 1.0):
            return x
        u = x
        for _ in range(8):                                  # Newton on x(u) = x
            dx = sample(x1, x2, u) - x
            d = (3 * (1 - 3 * x2 + 3 * x1) * u * u + 2 * (3 * x2 - 6 * x1) * u + 3 * x1)
            if abs(d) < 1e-6:
                break
            u = min(1.0, max(0.0, u - dx / d))
        return sample(y1, y2, u)
    return f


EXPO_OUT = bezier(0.16, 1, 0.3, 1)      # the house ease-out for entrances
SMOOTH = bezier(0.65, 0, 0.35, 1)       # in-out for moves
LINEAR = lambda p: clamp01(p)           # noqa: E731


def push(p):
    """Spring with heavy damping (no bounce) expressed over a normalised 0..1 range."""
    p = clamp01(p)
    return 1 - math.exp(-7 * p) * (1 + 7 * p) if p < 1 else 1.0


def interpolate(t, ts, vs, easing=None, clamp=True, posterize=None):
    """Keyframed value at time t. ts/vs are matching lists; easing is one function or a list of n-1.
    posterize=fps samples time on a coarser grid (deliberately choppy, hand-made motion)."""
    if posterize:
        t = math.floor(t * posterize) / posterize
    if t <= ts[0]:
        return vs[0] if clamp else vs[0] + (vs[1] - vs[0]) * (t - ts[0]) / (ts[1] - ts[0])
    if t >= ts[-1]:
        return vs[-1]
    for i in range(len(ts) - 1):
        if ts[i] <= t <= ts[i + 1]:
            e = easing[i] if isinstance(easing, (list, tuple)) else (easing or LINEAR)
            p = e((t - ts[i]) / max(1e-9, ts[i + 1] - ts[i]))
            return vs[i] + (vs[i + 1] - vs[i]) * p
    return vs[-1]


def pscale(p, s0, s1):
    """Perceptual scale: interpolate scale geometrically so growth looks even (s0, s1 > 0)."""
    s0, s1 = max(s0, 1e-3), max(s1, 1e-3)
    return s0 * (s1 / s0) ** p


# ---------------------------------------------------------------- frame clock + pencil "boil"
# Hand-drawn animation re-draws lines a few times per second, so they shimmer slightly ("line boil").
# The renderer calls set_time(t) every frame; pencil strokes cycle through BOIL_VARIANTS jitter seeds
# at BOIL_FPS (a posterized clock). Set BOIL_FPS = 0 to freeze lines.
CLOCK = {"t": 0.0}
BOIL_FPS = 6
BOIL_VARIANTS = 3


def set_time(t):
    CLOCK["t"] = t


def boil_seed(seed):
    if not BOIL_FPS:
        return seed
    return seed + 97 * (int(CLOCK["t"] * BOIL_FPS) % BOIL_VARIANTS)


# ---------------------------------------------------------------- fonts (LXGW WenKai, SIL OFL)
_TF = {}
_FONT = {}
FONT_FILES = {300: ROOT / "fonts/LXGWWenKai-Light.ttf", 400: ROOT / "fonts/LXGWWenKai-Regular.ttf",
              500: ROOT / "fonts/LXGWWenKai-Medium.ttf"}


def load_typeface(path):
    """Load from bytes: MakeFromFile fails on Windows when the path has non-ASCII characters."""
    return skia.Typeface.MakeFromData(skia.Data.MakeWithCopy(Path(path).read_bytes()))


def typeface(weight):
    k = 300 if weight < 380 else 400 if weight < 520 else 500
    if k not in _TF:
        _TF[k] = load_typeface(FONT_FILES[k])
    return _TF[k]


def font(family, weight, size):
    """family is kept for API compatibility; one handwritten family covers CJK + Latin.
    Weights >= 700 are drawn with synthetic emboldening (heavier pencil pressure)."""
    key = (int(weight), round(size, 1))
    f = _FONT.get(key)
    if f is None:
        f = skia.Font(typeface(weight), size)
        f.setSubpixel(True)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        f.setHinting(skia.FontHinting.kNone)
        if weight >= 700:
            f.setEmbolden(True)
        _FONT[key] = f
    return f


def fam_for(ch, family):
    return "hand"


def char_advances(s, size, weight, family="auto", tracking=0.0):
    f = font(family, weight, size)
    return [f.measureText(ch) + tracking * size for ch in s]


def text_width(s, size, weight=500, family="auto", tracking=0.0):
    adv = char_advances(s, size, weight, family, tracking)
    return sum(adv) - (tracking * size if s else 0)


# ---------------------------------------------------------------- paint helpers
# Over the full-frame presenter the same scene code draws light-on-dark: graphite becomes white chalk
# and every pencil colour switches to a brighter tint. Toggled with `with on_video():`.
VIDEO = {"on": False}
VIDEO_MAP = {INK: "#FFFFFF", MUTE: "#E4E4EA", BLUE: "#8CC0FF", GREEN: "#6BE39A", AMBER: "#FFB866",
             RED: "#FF7068", CYAN: "#78E6F0", MARKER: "#FFD84D"}


@contextmanager
def on_video():
    prev = VIDEO["on"]
    VIDEO["on"] = True
    try:
        yield
    finally:
        VIDEO["on"] = prev


def paint(color, a=1.0, stroke=None, blur=0.0):
    p = skia.Paint(AntiAlias=True)
    if VIDEO["on"] and isinstance(color, str):
        color = VIDEO_MAP.get(color, color)
    p.setColor(hexc(color, a) if isinstance(color, str) else color)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur > 0.05:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def pencil(color, a=1.0, width=3.0, seed=1, dash=None, jitter=1.0):
    """Stroke paint with a seeded wobble — a hand-drawn graphite / coloured-pencil line."""
    p = paint(color, a, stroke=width)
    eff = skia.DiscretePathEffect.Make(10.0, (0.55 + width * 0.18) * jitter, boil_seed(seed))
    if dash:
        eff = skia.PathEffect.MakeCompose(eff, skia.DashPathEffect.Make(dash, 0))
    p.setPathEffect(eff)
    return p


def sketch(c, path, color=INK, a=1.0, width=3.0, seed=1, dash=None):
    """Two offset pencil passes over the same path."""
    if a <= 0.003:
        return
    c.drawPath(path, pencil(color, a * 0.9, width, seed, dash))
    c.save()
    c.translate(0.7, 0.5)
    c.drawPath(path, pencil(color, a * 0.35, width * 0.55, seed + 7, dash, 1.6))
    c.restore()


def hatch(c, path, color=INK, a=0.3, spacing=9.0, angle=-40.0, width=1.6, seed=3):
    """Pencil hatching clipped to path."""
    if a <= 0.003:
        return
    b = path.computeTightBounds()
    c.save()
    c.clipPath(path, doAntiAlias=True)
    cx, cy = b.centerX(), b.centerY()
    c.translate(cx, cy)
    c.rotate(angle)
    r = math.hypot(b.width(), b.height()) / 2 + spacing
    p = pencil(color, a, width, seed, jitter=0.8)
    n = int(2 * r / spacing) + 1
    for i in range(n):
        y = -r + i * spacing
        ln = skia.Path()
        ln.moveTo(-r, y)
        ln.lineTo(r, y)
        c.drawPath(ln, p)
    c.restore()


def marker(c, x, y, w, h, p=1.0, color=MARKER, a=0.6):
    """Highlighter swash drawn left→right (multiply-blended like ink on paper)."""
    p = clamp01(p)
    if p <= 0 or a <= 0:
        return
    if VIDEO["on"]:
        y, h, a = y + h * 0.5, h * 0.55, 0.92
    path = skia.Path()
    ww = w * p
    path.moveTo(x + 4, y + 3)
    path.lineTo(x + ww, y)
    path.lineTo(x + ww - 4, y + h)
    path.lineTo(x, y + h - 2)
    path.close()
    pt = paint(color, a)
    if not VIDEO["on"]:
        pt.setBlendMode(skia.BlendMode.kMultiply)
    pt.setPathEffect(skia.DiscretePathEffect.Make(14, 1.2, 5))
    c.drawPath(path, pt)


@contextmanager
def layer(c, alpha=1.0, blur=0.0, scale=1.0, cx=W / 2, cy=H / 2, dx=0.0, dy=0.0):
    """Group transform + opacity + gaussian blur. Skips the offscreen when not needed."""
    if alpha <= 0.003:
        c.save()
        c.clipRect(skia.Rect.MakeEmpty())  # body still runs; everything it draws is rejected
        try:
            yield False
        finally:
            c.restore()
        return
    c.save()
    if dx or dy:
        c.translate(dx, dy)
    if scale != 1.0:
        c.translate(cx, cy)
        c.scale(scale, scale)
        c.translate(-cx, -cy)
    need = alpha < 0.997 or blur > 0.2
    if need:
        p = skia.Paint()
        p.setAlphaf(alpha)
        if blur > 0.2:
            p.setImageFilter(skia.ImageFilters.Blur(blur, blur))
        c.saveLayer(None, p)
    try:
        yield True
    finally:
        if need:
            c.restore()
        c.restore()


# ---------------------------------------------------------------- text
def draw_text(c, s, x, y, size, weight=500, color=INK, align="left", t=None, t0=None,
              stagger=0.028, rise=0.32, family="auto", tracking=0.0, alpha=1.0, blur_in=0.16,
              t1=None, out_dur=0.35, style="rise"):
    """Draw text at baseline y. If t0 is given, characters spring in one by one
    (rise + blur + fade; style="bounce" drops them in with overshoot, scale and a playful tilt).
    If t1 is given, the line blurs out after t1."""
    if not s or alpha <= 0.003:
        return 0
    adv = char_advances(s, size, weight, family, tracking)
    wid = sum(adv) - (tracking * size)
    if align == "center":
        x -= wid / 2
    elif align == "right":
        x -= wid
    oe = out_env(t, t1, out_dur) if t1 is not None else 1.0
    if oe <= 0.003:
        return wid
    f = font(family, weight, size)
    shadow = VIDEO["on"]
    cx = x
    for i, ch in enumerate(s):
        if ch != " ":
            rot, sc = 0.0, 1.0
            if t0 is not None:
                if style == "bounce":
                    k = spring(t - t0 - i * stagger, w=15, z=0.42)
                    ka = clamp01(k * 2.0)
                    oy = -(1 - k) * 0.9 * size
                    rot = (1 - k) * (18 if i % 2 else -14)
                    sc = 0.35 + 0.65 * k
                    bl = (1 - clamp01(k * 1.6)) * 0.08 * size
                else:
                    k = spring(t - t0 - i * stagger, w=12, z=0.86)
                    ka = clamp01(k * 1.25)
                    oy = (1 - k) * rise * size
                    bl = (1 - clamp01(k)) * blur_in * size
                if ka <= 0.003:
                    cx += adv[i]
                    continue
            else:
                ka, oy, bl = 1.0, 0.0, 0.0
            bl += (1 - oe) * 0.12 * size
            oy -= (1 - oe) * 0.18 * size
            a = alpha * ka * oe
            tilt = rot != 0.0 or sc != 1.0
            if tilt:
                c.save()
                px, py = cx + adv[i] / 2, y + oy - size * 0.35
                c.translate(px, py)
                c.rotate(rot)
                c.scale(sc, sc)
                c.translate(-px, -py)
            if shadow:
                sp = skia.Paint(AntiAlias=True, Color=hexc("#000000", 0.55 * a))
                sp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, max(2.0, size * 0.06) + bl))
                c.drawString(ch, cx + size * 0.02, y + oy + size * 0.04, f, sp)
            c.drawString(ch, cx, y + oy, f, paint(color, a, blur=bl))
            if tilt:
                c.restore()
        cx += adv[i]
    return wid


def draw_label(c, s, x, y, size=24, color=BLUE, align="left", t=None, t0=None, alpha=1.0, t1=None):
    """Small kicker with wide tracking."""
    return draw_text(c, s, x, y, size * 1.12, 500, color, align, t, t0, stagger=0.012, rise=0.4,
                     tracking=0.12, alpha=alpha, t1=t1)


# ---------------------------------------------------------------- shapes
def rrect(x, y, w, h, r):
    return skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)


def rrect_path(x, y, w, h, r):
    p = skia.Path()
    p.addRRect(rrect(x, y, w, h, r))
    return p


def _mix_white(col, k):
    col = col.lstrip("#")
    rgb = [int(col[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{int(255 + (v - 255) * k):02X}" for v in rgb)


def glass(c, x, y, w, h, r=36, alpha=1.0, tint=None, stroke_a=0.10, fill_a=0.045, glow=None, seed=None):
    """Paper card pinned on the whiteboard: soft shadow, paper fill, pencil outline."""
    if alpha <= 0.003:
        return
    seed = seed if seed is not None else int(x * 7 + y * 3) % 97 + 1
    c.drawRRect(rrect(x + 3, y + 8, w, h, r), paint("#5A6478", 0.13 * alpha, blur=14))
    c.drawRRect(rrect(x, y, w, h, r), paint(_mix_white(tint, 0.07) if tint else "#FFFFFF", 0.96 * alpha))
    col = glow or INK
    sketch(c, rrect_path(x, y, w, h, r), col, alpha * (0.55 + stroke_a), 2.4 if glow else 2.0, seed)


def pill(c, x, y, s, size=30, color=INK, bg=None, t=None, t0=None, align="center", alpha=1.0,
         weight=600, t1=None, pad=26):
    """Rounded tag that scales in with a spring. (x, y) is its center."""
    k = 1.0 if t0 is None else spring(t - t0, w=13, z=0.72)
    oe = out_env(t, t1) if t1 is not None else 1.0
    a = alpha * clamp01(k * 1.4) * oe
    if a <= 0.003:
        return
    tw = text_width(s, size, weight)
    w, h = tw + pad * 2, size * 1.9
    if align == "left":
        x += w / 2
    sc = 0.86 + 0.14 * k
    bgc = bg or color
    with layer(c, a, (1 - clamp01(k)) * 8 + (1 - oe) * 8, sc, x, y):
        c.drawRRect(rrect(x - w / 2, y - h / 2, w, h, h / 2), paint(_mix_white(bgc, 0.14), 1))
        sketch(c, rrect_path(x - w / 2, y - h / 2, w, h, h / 2), bgc, 0.85, 2.2, int(x) % 50 + 3)
        draw_text(c, s, x, y + size * 0.36, size, weight, color, "center")
    return w


def line_draw(c, pts, p, color=INK, a=1.0, width=3, dash=None):
    """Pencil polyline drawn progressively (p in 0..1)."""
    if p <= 0 or a <= 0:
        return
    path = skia.Path()
    path.moveTo(*pts[0])
    for q in pts[1:]:
        path.lineTo(*q)
    meas = skia.PathMeasure(path, False)
    L = meas.getLength()
    seg = skia.Path()
    meas.getSegment(0, L * clamp01(p), seg, True)
    sketch(c, seg, color, a, width, int(pts[0][0] + pts[0][1]) % 61 + 2, dash)


def arc(c, cx, cy, r, start, sweep, color, a=1.0, width=6):
    if sweep == 0 or a <= 0:
        return
    p = skia.Path()
    if abs(sweep) >= 359.9:
        p.addCircle(cx, cy, r)
    else:
        p.addArc(skia.Rect.MakeXYWH(cx - r, cy - r, 2 * r, 2 * r), start, sweep)
    sketch(c, p, color, a, width, 11)


def check(c, x, y, s, p, color=GREEN, a=1.0):
    line_draw(c, [(x - 0.42 * s, y), (x - 0.12 * s, y + 0.3 * s), (x + 0.45 * s, y - 0.35 * s)],
              p, color, a, width=max(3, s * 0.16))


def cross(c, x, y, s, p, color=RED, a=1.0):
    line_draw(c, [(x - s / 2, y - s / 2), (x + s / 2, y + s / 2)], clamp01(p * 2), color, a, max(3, s * 0.14))
    line_draw(c, [(x + s / 2, y - s / 2), (x - s / 2, y + s / 2)], clamp01(p * 2 - 1), color, a, max(3, s * 0.14))


def neq(c, x, y, s, p, color=RED, a=1.0):
    """Not-equal sign drawn on."""
    wdt = max(4, s * 0.11)
    line_draw(c, [(x - s / 2, y - s * 0.17), (x + s / 2, y - s * 0.17)], clamp01(p * 3), color, a, wdt)
    line_draw(c, [(x - s / 2, y + s * 0.17), (x + s / 2, y + s * 0.17)], clamp01(p * 3 - 1), color, a, wdt)
    line_draw(c, [(x + s * 0.22, y - s * 0.5), (x - s * 0.22, y + s * 0.5)], clamp01(p * 3 - 2), color, a, wdt)


def arrow(c, x0, y0, x1, y1, p, color=MUTE, a=1.0, width=3, head=14):
    if p <= 0:
        return
    xe, ye = lerp(x0, x1, clamp01(p)), lerp(y0, y1, clamp01(p))
    line_draw(c, [(x0, y0), (xe, ye)], 1, color, a, width)
    ang = math.atan2(y1 - y0, x1 - x0)
    hp = clamp01(p * 1.2 - 0.2)
    if hp > 0:
        for s in (2.5, -2.5):
            line_draw(c, [(xe, ye), (xe - head * math.cos(ang + s / 5 * 1.2), ye - head * math.sin(ang + s / 5 * 1.2))],
                      hp, color, a, width)


# ---------------------------------------------------------------- doodles (hand-drawn emphasis)
def doodle_circle(c, cx, cy, rx, ry, p, color=RED, a=1.0, width=4, seed=5):
    """A quick loop drawn around a word: a bit more than one turn, slightly tilted, never closed neatly."""
    p = clamp01(p)
    if p <= 0:
        return
    path = skia.Path()
    turns, n = 1.15, 72
    for i in range(n + 1):
        u = i / n
        ang = -2.2 + u * turns * 2 * math.pi
        wob = 1 + 0.05 * math.sin(u * 9 + seed)
        x = cx + rx * wob * math.cos(ang) + u * rx * 0.08
        y = cy + ry * wob * math.sin(ang) - u * ry * 0.1
        (path.moveTo if i == 0 else path.lineTo)(x, y)
    meas = skia.PathMeasure(path, False)
    seg = skia.Path()
    meas.getSegment(0, meas.getLength() * p, seg, True)
    sketch(c, seg, color, a, width, seed)


def squiggle(c, x0, x1, y, p, color=BLUE, a=1.0, width=4, amp=7, wl=26, seed=3):
    """Wavy underline drawn left to right."""
    p = clamp01(p)
    if p <= 0:
        return
    xe = lerp(x0, x1, p)
    path = skia.Path()
    n = max(2, int((xe - x0) / 4))
    for i in range(n + 1):
        x = lerp(x0, xe, i / n)
        yy = y + amp * math.sin((x - x0) / wl * 2 * math.pi)
        (path.moveTo if i == 0 else path.lineTo)(x, yy)
    sketch(c, path, color, a, width, seed)


def sparkle(c, x, y, s, t, t0, color=MARKER, a=1.0):
    """Four-point star that pops, spins a little and twinkles."""
    k = spring(t - t0, w=16, z=0.45)
    if k <= 0.01:
        return
    tw = 0.85 + 0.15 * math.sin((t - t0) * 7)
    r = s * clamp01(k) * tw
    c.save()
    c.translate(x, y)
    c.rotate((1 - k) * 90 + (t - t0) * 20)
    path = skia.Path()
    for i in range(8):
        ang = i * math.pi / 4
        rr = r if i % 2 == 0 else r * 0.28
        (path.moveTo if i == 0 else path.lineTo)(rr * math.cos(ang), rr * math.sin(ang))
    path.close()
    c.drawPath(path, paint(color, a * clamp01(k * 2)))
    c.restore()


def burst(c, x, y, r0, r1, n, t, t0, color=MARKER, a=1.0, width=4, rot=0.0):
    """Comic 'action lines' radiating out once."""
    p = ease_out((t - t0) / 0.45)
    fade = 1 - ease_out((t - t0 - 0.35) / 0.5)
    if p <= 0 or fade <= 0:
        return
    for i in range(n):
        ang = rot + 2 * math.pi * i / n
        ra, rb = lerp(r0, r1, p * 0.55), lerp(r0, r1, p)
        ln = skia.Path()
        ln.moveTo(x + ra * math.cos(ang), y + ra * math.sin(ang))
        ln.lineTo(x + rb * math.cos(ang), y + rb * math.sin(ang))
        sketch(c, ln, color, a * fade, width, 50 + i)


# ---------------------------------------------------------------- objects
def bottle(c, cx, base, w, h, color, label, sub, side=1.0, alpha=1.0, back_lines=None, scan=None):
    """Pencil-sketched vitamin bottle. side = cos(rotation) in [-1, 1]; < 0 shows the back label."""
    if alpha <= 0.003:
        return
    sx = max(0.02, abs(side))
    c.save()
    c.translate(cx, base)
    c.scale(sx, 1)
    x, y = -w / 2, -h
    body = rrect_path(x, y + h * 0.16, w, h * 0.84, w * 0.16)
    c.drawPath(body, paint("#FFFFFF", 0.97 * alpha))
    # side shading
    shade = skia.Path()
    shade.addRect(skia.Rect.MakeLTRB(x + w * 0.62, y, x + w, y + h))
    hatch(c, skia.Op(body, shade, skia.PathOp.kIntersect_PathOp) or body, INK, 0.22 * alpha, 8, -55, 1.3, 4)
    sketch(c, body, INK, 0.85 * alpha, 2.6, 21)
    # cap
    cap = rrect_path(x + w * 0.16, y, w * 0.68, h * 0.14, w * 0.06)
    c.drawPath(cap, paint(_mix_white(color, 0.25), alpha))
    hatch(c, cap, color, 0.75 * alpha, 7, 90, 2.0, 8)
    sketch(c, cap, INK, 0.8 * alpha, 2.4, 22)
    # label
    lx, ly, lw, lh = x + w * 0.08, y + h * 0.36, w * 0.84, h * 0.44
    c.drawRRect(rrect(lx, ly, lw, lh, 10), paint(_mix_white(color, 0.10), alpha))
    sketch(c, rrect_path(lx, ly, lw, lh, 10), color, 0.9 * alpha, 2.2, 23)
    if side >= 0:
        draw_text(c, label, 0, ly + lh * 0.5, w * 0.2, 800, color, "center", alpha=alpha)
        draw_text(c, sub, 0, ly + lh * 0.8, w * 0.085, 500, MUTE, "center", alpha=alpha)
    else:
        c.scale(-1, 1)  # back label reads correctly
        lines = back_lines or []
        for i, (txt, wfrac) in enumerate(lines):
            yy = ly + 26 + i * (lh - 40) / max(1, len(lines))
            ln = skia.Path()
            ln.moveTo(-lw / 2 + 14, yy)
            ln.lineTo(-lw / 2 + 14 + (lw - 28) * wfrac, yy)
            sketch(c, ln, INK if i == 0 else MUTE, (0.85 if i == 0 else 0.6) * alpha, 4 if i == 0 else 3, 30 + i)
        if scan is not None and 0 < scan < 1:
            sy = ly + lh * scan
            marker(c, -lw / 2 - 6, sy - 9, lw + 12, 18, 1, CYAN, 0.35 * alpha)
            ln = skia.Path()
            ln.moveTo(-lw / 2 - 6, sy)
            ln.lineTo(lw / 2 + 6, sy)
            sketch(c, ln, CYAN, alpha, 2.5, 40)
    c.restore()


def tablet(c, cx, cy, r, color=INK, alpha=1.0, label=None, score=True, glow=False):
    if alpha <= 0.003:
        return
    if glow:
        c.drawCircle(cx, cy, r * 1.18, paint(MARKER, 0.55 * alpha))
    circ = skia.Path()
    circ.addCircle(cx, cy, r)
    c.drawPath(circ, paint("#FFFFFF", alpha))
    moon = skia.Path()
    moon.addCircle(cx - r * 0.28, cy - r * 0.3, r * 1.02)
    shade = skia.Op(circ, moon, skia.PathOp.kDifference_PathOp)
    if shade:
        hatch(c, shade, INK, 0.35 * alpha, max(4, r * 0.11), -45, max(1.1, r * 0.025), 6)
    sketch(c, circ, INK, 0.85 * alpha, max(2, r * 0.045), int(cx) % 40 + 2)
    if score:
        ln = skia.Path()
        ln.moveTo(cx - r * 0.62, cy)
        ln.lineTo(cx + r * 0.62, cy)
        sketch(c, ln, INK, 0.55 * alpha, max(1.5, r * 0.04), 9)
    if label:
        draw_text(c, label, cx, cy + r + r * 0.55 + 10, max(20, r * 0.42), 600, color, "center", alpha=alpha)


def form_icon(c, kind, cx, cy, s, t, color=INK, alpha=1.0):
    """Pencil icons for the six dosage forms. s ~ icon half-size."""
    if alpha <= 0.003:
        return
    sw = max(2.5, s * 0.05)
    seed = {"plain": 3, "sr": 5, "coated": 7, "lipo": 11, "gummy": 13, "liquid": 17}[kind]

    def S(path, a=1.0, w=sw):
        sketch(c, path, color, alpha * a, w, seed)

    if kind == "plain":
        p = skia.Path()
        p.addCircle(cx, cy, s * 0.62)
        hatch(c, p, color, 0.18 * alpha, 8, -40, 1.4, seed)
        S(p)
        ln = skia.Path()
        ln.moveTo(cx - s * 0.4, cy)
        ln.lineTo(cx + s * 0.4, cy)
        S(ln, 0.8)
    elif kind == "sr":  # sustained release: layered core + released particles
        for i, rr in enumerate((0.62, 0.44, 0.26)):
            S(rrect_path(cx - s * rr * 1.25, cy - s * rr * 0.8, s * rr * 2.5, s * rr * 1.6, s * rr * 0.8), 1 - i * 0.25)
        for i in range(5):
            ph = (t * 0.35 + i / 5) % 1
            x = cx + s * (0.85 + ph * 0.45)
            y = cy + s * 0.5 * math.sin(i * 2.1)
            c.drawCircle(x, y, s * 0.05, paint(color, alpha * (1 - ph) * 0.9))
    elif kind == "coated":
        outer = rrect_path(cx - s * 0.78, cy - s * 0.48, s * 1.56, s * 0.96, s * 0.48)
        inner = rrect_path(cx - s * 0.6, cy - s * 0.3, s * 1.2, s * 0.6, s * 0.3)
        ring = skia.Op(outer, inner, skia.PathOp.kDifference_PathOp)
        if ring:
            hatch(c, ring, color, 0.3 * alpha, 7, -40, 1.4, seed)
        S(outer)
        S(inner, 0.6)
    elif kind == "lipo":
        n = 18
        for i in range(n):
            a = t * 0.25 + 2 * math.pi * i / n
            for rr, ra in ((0.66, 1.0), (0.48, 0.6)):
                x, y = cx + s * rr * math.cos(a), cy + s * rr * math.sin(a)
                cp = skia.Path()
                cp.addCircle(x, y, s * 0.065)
                S(cp, ra, sw * 0.6)
        core = skia.Path()
        core.addCircle(cx, cy, s * 0.2)
        hatch(c, core, color, 0.5 * alpha, 5, -40, 1.3, seed)
        S(core)
    elif kind == "gummy":
        p = skia.Path()
        p.addCircle(cx, cy - s * 0.42, s * 0.26)
        p.addCircle(cx - s * 0.2, cy - s * 0.62, s * 0.1)
        p.addCircle(cx + s * 0.2, cy - s * 0.62, s * 0.1)
        p.addRRect(rrect(cx - s * 0.34, cy - s * 0.22, s * 0.68, s * 0.8, s * 0.3))
        p.addCircle(cx - s * 0.42, cy - s * 0.05, s * 0.12)
        p.addCircle(cx + s * 0.42, cy - s * 0.05, s * 0.12)
        p.addCircle(cx - s * 0.22, cy + s * 0.6, s * 0.14)
        p.addCircle(cx + s * 0.22, cy + s * 0.6, s * 0.14)
        merged = skia.Op(p, skia.Path(), skia.PathOp.kUnion_PathOp) or p
        hatch(c, merged, AMBER if color == INK else color, 0.3 * alpha, 7, -40, 1.5, seed)
        S(merged)
    elif kind == "liquid":
        p = skia.Path()
        p.moveTo(cx, cy - s * 0.78)
        p.cubicTo(cx + s * 0.18, cy - s * 0.42, cx + s * 0.55, cy - s * 0.05, cx + s * 0.55, cy + s * 0.24)
        p.cubicTo(cx + s * 0.55, cy + s * 0.56, cx + s * 0.3, cy + s * 0.78, cx, cy + s * 0.78)
        p.cubicTo(cx - s * 0.3, cy + s * 0.78, cx - s * 0.55, cy + s * 0.56, cx - s * 0.55, cy + s * 0.24)
        p.cubicTo(cx - s * 0.55, cy - s * 0.05, cx - s * 0.18, cy - s * 0.42, cx, cy - s * 0.78)
        lv = cy + s * 0.2 + s * 0.05 * math.sin(t * 2.4)
        water = skia.Path()
        water.addRect(skia.Rect.MakeLTRB(cx - s, lv, cx + s, cy + s))
        wp = skia.Op(p, water, skia.PathOp.kIntersect_PathOp)
        if wp:
            hatch(c, wp, BLUE if color == INK else color, 0.45 * alpha, 6, 0, 1.4, seed)
        S(p)
