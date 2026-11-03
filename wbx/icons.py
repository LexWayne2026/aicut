"""Pencil icon library. Every icon is drawn ON: strokes trace in order (like a hand drawing it),
then the accent hatching fades in. Icons are defined in a 100x100 box.

    draw_icon(c, "bulb", cx, cy, size=120, p=progress, color=INK, accent=MARKER, t=t)
    icon_in(c, "bulb", cx, cy, 120, t, t0)        # draw-on + gentle pop, driven by time
    ICONS.keys()                                  # every available name

Names: bottle pill tablet capsule coin coins price_tag cart wallet money_bag magnifier clipboard
document shield heart brain bulb flask leaf drop clock calendar chart_bar chart_pie chart_line person
people thumbs_up warning star target scale gift home apple bowl stomach question exclaim speech
check_circle cross_circle trophy rocket gear lock dna atom
"""
import math

import skia

from .core import AMBER, BLUE, CYAN, GREEN, INK, MARKER, RED, clamp01, hatch, spring, sketch

# ------------------------------------------------------------------ path helpers (100x100 box)


def _p():
    return skia.Path()


def circle(cx, cy, r):
    p = _p()
    p.addCircle(cx, cy, r)
    return p


def oval(x, y, w, h):
    p = _p()
    p.addOval(skia.Rect.MakeXYWH(x, y, w, h))
    return p


def rr(x, y, w, h, r):
    p = _p()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r))
    return p


def poly(*pts, close=False):
    p = _p()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def arcp(cx, cy, r, start, sweep):
    p = _p()
    p.addArc(skia.Rect.MakeXYWH(cx - r, cy - r, 2 * r, 2 * r), start, sweep)
    return p


def curve(*pts):
    """Quadratic chain: p0, c1, p1, c2, p2 ..."""
    p = _p()
    p.moveTo(*pts[0])
    for i in range(1, len(pts) - 1, 2):
        p.quadTo(*pts[i], *pts[i + 1])
    return p


def heart_path(cx, cy, s):
    p = _p()
    p.moveTo(cx, cy + s * 0.35)
    p.cubicTo(cx - s * 0.9, cy - s * 0.25, cx - s * 0.45, cy - s * 0.95, cx, cy - s * 0.42)
    p.cubicTo(cx + s * 0.45, cy - s * 0.95, cx + s * 0.9, cy - s * 0.25, cx, cy + s * 0.35)
    p.close()
    return p


def star_path(cx, cy, r, inner=0.45, n=5):
    p = _p()
    for i in range(n * 2):
        a = -math.pi / 2 + i * math.pi / n
        rr_ = r if i % 2 == 0 else r * inner
        (p.moveTo if i == 0 else p.lineTo)(cx + rr_ * math.cos(a), cy + rr_ * math.sin(a))
    p.close()
    return p


# ------------------------------------------------------------------ icon definitions
# each returns (strokes, fills); fills are (path, accent?) — accent=True uses the accent colour


def _bottle():
    body = rr(28, 30, 44, 60, 9)
    cap = rr(34, 14, 32, 16, 4)
    label = rr(32, 46, 36, 26, 4)
    return [cap, body, label, poly((40, 54), (60, 54)), poly((40, 62), (55, 62))], [(cap, True)]


def _pill():
    body = rr(16, 36, 68, 28, 14)
    half = rr(50, 36, 34, 28, 14)
    return [body, poly((50, 37), (50, 63))], [(half, True)]


def _tablet():
    c = circle(50, 50, 30)
    return [c, poly((30, 50), (70, 50))], [(c, True)]


def _capsule():
    p = rr(14, 38, 72, 24, 12)
    p2 = _p()
    p2.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(14, 38, 72, 24), 12, 12))
    m = skia.Matrix.RotateDeg(-30, skia.Point(50, 50))
    p.transform(m)
    half = rr(50, 38, 36, 24, 12)
    half.transform(m)
    seam = poly((50, 39), (50, 61))
    seam.transform(m)
    return [p, seam], [(half, True)]


def _coin():
    c = circle(50, 50, 32)
    return [c, circle(50, 50, 24), poly((42, 40), (50, 50), (58, 40)), poly((40, 52), (60, 52)),
            poly((40, 60), (60, 60)), poly((50, 50), (50, 68))], [(c, True)]


def _coins():
    s1 = oval(22, 58, 56, 18)
    s2 = oval(22, 46, 56, 18)
    s3 = oval(22, 34, 56, 18)
    return [s1, poly((22, 67), (22, 55)), poly((78, 67), (78, 55)), s2, poly((22, 55), (22, 43)),
            poly((78, 55), (78, 43)), s3], [(s3, True)]


def _price_tag():
    p = poly((18, 50), (40, 26), (82, 26), (82, 74), (40, 74), close=True)
    return [p, circle(34, 50, 5), poly((50, 44), (72, 44)), poly((50, 56), (66, 56))], [(p, True)]


def _cart():
    basket = poly((18, 26), (28, 26), (36, 62), (76, 62), (82, 36), (31, 36))
    return [basket, oval(33, 68, 14, 13), oval(63, 68, 14, 13)], [(poly((31, 36), (82, 36), (76, 62), (36, 62),
                                                                     close=True), True)]


def _wallet():
    b = rr(16, 30, 68, 46, 8)
    flap = rr(56, 44, 30, 18, 6)
    return [b, flap, circle(66, 53, 3)], [(flap, True)]


def _money_bag():
    bag = curve((40, 30), (14, 52), (22, 76), (50, 90), (78, 76), (86, 52), (60, 30))
    bag.close()
    return [bag, poly((40, 30), (36, 18), (64, 18), (60, 30)), poly((44, 50), (50, 58), (56, 50)),
            poly((42, 62), (58, 62)), poly((50, 58), (50, 74))], [(bag, True)]


def _magnifier():
    lens = circle(42, 42, 22)
    return [lens, poly((58, 58), (82, 82)), arcp(42, 42, 14, 200, 60)], [(lens, True)]


def _clipboard():
    b = rr(24, 18, 52, 70, 6)
    clip = rr(38, 12, 24, 12, 4)
    lines = [poly((34, 40), (38, 44), (46, 34)), poly((52, 40), (68, 40)), poly((34, 56), (38, 60), (46, 50)),
             poly((52, 56), (68, 56)), poly((34, 72), (68, 72))]
    return [b, clip] + lines, [(clip, True)]


def _document():
    p = poly((26, 14), (62, 14), (76, 28), (76, 86), (26, 86), close=True)
    return [p, poly((62, 14), (62, 28), (76, 28)), poly((36, 42), (66, 42)), poly((36, 54), (66, 54)),
            poly((36, 66), (56, 66))], [(poly((62, 14), (76, 28), (62, 28), close=True), True)]


def _shield():
    p = _p()
    p.moveTo(50, 12)
    p.lineTo(80, 24)
    p.cubicTo(80, 56, 68, 78, 50, 88)
    p.cubicTo(32, 78, 20, 56, 20, 24)
    p.close()
    return [p, poly((36, 50), (46, 60), (66, 38))], [(p, True)]


def _heart():
    h = heart_path(50, 58, 64)
    return [h, poly((24, 52), (38, 52), (44, 42), (52, 64), (58, 50), (76, 50))], [(h, True)]


def _brain():
    left = curve((50, 22), (30, 16), (24, 34), (12, 44), (22, 58), (18, 76), (38, 78), (46, 86), (50, 80))
    right = curve((50, 22), (70, 16), (76, 34), (88, 44), (78, 58), (82, 76), (62, 78), (54, 86), (50, 80))
    return [left, right, poly((50, 22), (50, 80)), curve((30, 40), (40, 44), (36, 54)),
            curve((70, 40), (60, 44), (64, 54))], [(left, True)]


def _bulb():
    glass = curve((38, 66), (24, 52), (26, 36), (30, 14), (50, 14), (70, 14), (74, 36), (76, 52), (62, 66))
    glass.close()
    return [glass, poly((38, 66), (62, 66)), poly((40, 74), (60, 74)), poly((43, 82), (57, 82)),
            poly((44, 48), (50, 56), (56, 48)), poly((50, 56), (50, 66))], [(glass, True)]


def _flask():
    p = poly((40, 14), (40, 42), (20, 82), (80, 82), (60, 42), (60, 14))
    liquid = poly((29, 64), (71, 64), (80, 82), (20, 82), close=True)
    return [p, poly((34, 14), (66, 14)), poly((29, 64), (71, 64))], [(liquid, True)]


def _leaf():
    p = curve((20, 80), (20, 20), (80, 20), (80, 80), (20, 80))
    p.close()
    return [p, poly((20, 80), (66, 34)), poly((40, 60), (40, 44)), poly((52, 48), (64, 48))], [(p, True)]


def _drop():
    p = _p()
    p.moveTo(50, 12)
    p.cubicTo(60, 30, 76, 46, 76, 62)
    p.cubicTo(76, 78, 64, 88, 50, 88)
    p.cubicTo(36, 88, 24, 78, 24, 62)
    p.cubicTo(24, 46, 40, 30, 50, 12)
    p.close()
    return [p, arcp(50, 64, 14, 100, 70)], [(p, True)]


def _clock():
    c = circle(50, 50, 34)
    return [c, poly((50, 30), (50, 50), (64, 58))], [(c, True)]


def _calendar():
    b = rr(18, 22, 64, 62, 6)
    top = rr(18, 22, 64, 16, 6)
    return [b, poly((18, 38), (82, 38)), poly((34, 14), (34, 28)), poly((66, 14), (66, 28)),
            poly((32, 52), (40, 52)), poly((48, 52), (56, 52)), poly((64, 52), (70, 52)),
            poly((32, 66), (40, 66)), poly((48, 66), (56, 66))], [(top, True)]


def _chart_bar():
    bars = [rr(20, 54, 14, 30, 2), rr(43, 36, 14, 48, 2), rr(66, 20, 14, 64, 2)]
    return [poly((12, 86), (90, 86))] + bars, [(bars[2], True)]


def _chart_pie():
    c = circle(50, 50, 34)
    wedge = _p()
    wedge.moveTo(50, 50)
    wedge.arcTo(skia.Rect.MakeXYWH(16, 16, 68, 68), -90, 110, False)
    wedge.close()
    return [c, poly((50, 50), (50, 16)), poly((50, 50), (50 + 34 * math.cos(math.radians(20)),
                                                        50 + 34 * math.sin(math.radians(20))))], [(wedge, True)]


def _chart_line():
    return [poly((14, 86), (14, 14)), poly((14, 86), (88, 86)), poly((20, 72), (38, 54), (54, 62), (82, 26)),
            poly((70, 26), (82, 26), (82, 38))], []


def _person():
    head = circle(50, 30, 14)
    body = curve((22, 88), (22, 52), (50, 50), (78, 52), (78, 88))
    return [head, body], [(head, True)]


def _people():
    return [circle(36, 34, 12), curve((14, 84), (14, 52), (36, 52), (58, 52), (58, 84)),
            circle(66, 30, 11), curve((56, 50), (72, 46), (86, 56), (88, 66), (88, 80))], [(circle(36, 34, 12), True)]


def _thumbs_up():
    hand = poly((36, 46), (48, 18), (56, 20), (54, 42), (78, 42), (82, 50), (74, 84), (36, 84), close=True)
    cuff = rr(16, 44, 20, 42, 3)
    return [cuff, hand], [(cuff, True)]


def _warning():
    t = poly((50, 14), (88, 82), (12, 82), close=True)
    return [t, poly((50, 38), (50, 60)), circle(50, 70, 2)], [(t, True)]


def _star():
    s = star_path(50, 52, 38)
    return [s], [(s, True)]


def _target():
    return [circle(50, 50, 36), circle(50, 50, 24), circle(50, 50, 11), poly((50, 50), (84, 16)),
            poly((76, 14), (84, 16), (86, 24))], [(circle(50, 50, 11), True)]


def _scale():
    return [poly((50, 16), (50, 82)), poly((32, 84), (68, 84)), poly((18, 30), (82, 30)),
            poly((18, 30), (8, 56)), poly((18, 30), (28, 56)), arcp(18, 56, 10, 0, 180),
            poly((82, 30), (72, 56)), poly((82, 30), (92, 56)), arcp(82, 56, 10, 0, 180)], \
        [(arcp(18, 56, 10, 0, 180), True)]


def _gift():
    box = rr(18, 40, 64, 44, 4)
    lid = rr(14, 28, 72, 14, 3)
    return [box, lid, poly((50, 28), (50, 84)), curve((50, 28), (36, 10), (34, 26), (50, 28)),
            curve((50, 28), (64, 10), (66, 26), (50, 28))], [(lid, True)]


def _home():
    roof = poly((12, 50), (50, 18), (88, 50))
    body = poly((22, 42), (22, 84), (78, 84), (78, 42))
    door = rr(42, 58, 16, 26, 2)
    return [roof, body, door], [(door, True)]


def _apple():
    p = _p()
    p.moveTo(50, 34)
    p.cubicTo(30, 22, 12, 36, 18, 60)
    p.cubicTo(24, 82, 40, 90, 50, 82)
    p.cubicTo(60, 90, 76, 82, 82, 60)
    p.cubicTo(88, 36, 70, 22, 50, 34)
    p.close()
    leaf = curve((52, 28), (56, 12), (70, 12), (64, 26), (52, 28))
    return [p, poly((50, 34), (52, 20)), leaf], [(p, True)]


def _bowl():
    b = curve((12, 50), (14, 86), (50, 86), (86, 86), (88, 50))
    b.close()
    return [b, curve((30, 40), (34, 30), (30, 22)), curve((50, 40), (54, 30), (50, 20)),
            curve((70, 40), (74, 30), (70, 22))], [(b, True)]


def _stomach():
    p = curve((40, 14), (40, 30), (30, 36), (14, 48), (24, 70), (40, 88), (64, 78), (86, 66), (78, 44),
              (72, 32), (60, 40), (54, 44), (52, 30))
    return [p, poly((52, 30), (52, 14))], [(p, True)]


def _question():
    q = curve((32, 34), (32, 14), (50, 14), (70, 14), (70, 32), (70, 46), (50, 54), (50, 62), (50, 66))
    return [circle(50, 50, 42), q, circle(50, 78, 2.5)], []


def _exclaim():
    return [circle(50, 50, 42), poly((50, 22), (50, 60)), circle(50, 74, 2.5)], [(circle(50, 50, 42), True)]


def _speech():
    b = rr(12, 18, 76, 52, 14)
    tail = poly((30, 70), (24, 88), (46, 70))
    return [b, tail, poly((28, 38), (72, 38)), poly((28, 50), (58, 50))], [(b, True)]


def _check_circle():
    c = circle(50, 50, 36)
    return [c, poly((32, 52), (45, 64), (70, 36))], [(c, True)]


def _cross_circle():
    c = circle(50, 50, 36)
    return [c, poly((36, 36), (64, 64)), poly((64, 36), (36, 64))], [(c, True)]


def _trophy():
    cup = curve((28, 18), (26, 60), (50, 62), (74, 60), (72, 18))
    cup.close()
    return [cup, curve((28, 26), (12, 26), (16, 40), (20, 50), (30, 50)),
            curve((72, 26), (88, 26), (84, 40), (80, 50), (70, 50)), poly((50, 62), (50, 76)),
            rr(34, 76, 32, 10, 2)], [(cup, True)]


def _rocket():
    body = curve((50, 10), (76, 34), (66, 72), (50, 74), (34, 72), (24, 34), (50, 10))
    return [body, circle(50, 40, 8), poly((34, 62), (20, 80), (38, 72)), poly((66, 62), (80, 80), (62, 72)),
            poly((44, 76), (50, 92), (56, 76))], [(circle(50, 40, 8), True)]


def _gear():
    p = _p()
    n = 8
    for i in range(n * 2):
        a = i * math.pi / n
        r = 38 if i % 2 == 0 else 30
        for da in (-0.16, 0.16):
            x, y = 50 + r * math.cos(a + da), 50 + r * math.sin(a + da)
            (p.moveTo if (i == 0 and da < 0) else p.lineTo)(x, y)
    p.close()
    return [p, circle(50, 50, 12)], [(circle(50, 50, 12), True)]


def _lock():
    b = rr(24, 44, 52, 40, 6)
    return [arcp(50, 44, 16, 180, 180), poly((34, 44), (34, 44)), b, circle(50, 62, 4), poly((50, 66), (50, 74))], \
        [(b, True)]


def _dna():
    a, b = _p(), _p()
    for i in range(41):
        y = 12 + i * 1.9
        x1 = 50 + 22 * math.sin(i / 40 * 2.2 * math.pi)
        x2 = 50 - 22 * math.sin(i / 40 * 2.2 * math.pi)
        (a.moveTo if i == 0 else a.lineTo)(x1, y)
        (b.moveTo if i == 0 else b.lineTo)(x2, y)
    rungs = []
    for i in range(2, 40, 5):
        y = 12 + i * 1.9
        x1 = 50 + 22 * math.sin(i / 40 * 2.2 * math.pi)
        rungs.append(poly((x1, y), (100 - x1, y)))
    return [a, b] + rungs, []


def _atom():
    orbits = []
    for ang in (0, 60, 120):
        o = oval(14, 38, 72, 24)
        o.transform(skia.Matrix.RotateDeg(ang, skia.Point(50, 50)))
        orbits.append(o)
    nuc = circle(50, 50, 7)
    return orbits + [nuc], [(nuc, True)]


ICONS = dict(bottle=_bottle, pill=_pill, tablet=_tablet, capsule=_capsule, coin=_coin, coins=_coins,
             price_tag=_price_tag, cart=_cart, wallet=_wallet, money_bag=_money_bag, magnifier=_magnifier,
             clipboard=_clipboard, document=_document, shield=_shield, heart=_heart, brain=_brain, bulb=_bulb,
             flask=_flask, leaf=_leaf, drop=_drop, clock=_clock, calendar=_calendar, chart_bar=_chart_bar,
             chart_pie=_chart_pie, chart_line=_chart_line, person=_person, people=_people,
             thumbs_up=_thumbs_up, warning=_warning, star=_star, target=_target, scale=_scale, gift=_gift,
             home=_home, apple=_apple, bowl=_bowl, stomach=_stomach, question=_question, exclaim=_exclaim,
             speech=_speech, check_circle=_check_circle, cross_circle=_cross_circle, trophy=_trophy,
             rocket=_rocket, gear=_gear, lock=_lock, dna=_dna, atom=_atom)
_CACHE = {}


def _get(name):
    if name not in _CACHE:
        _CACHE[name] = ICONS[name]()
    return _CACHE[name]


def draw_icon(c, name, cx, cy, size=120, p=1.0, color=INK, accent=MARKER, alpha=1.0, width=None, seed=None):
    """Draw icon `name` centred at (cx, cy), `size` design units wide. p = draw-on progress 0..1:
    strokes trace in order over the first 80%, the accent hatch fades in over the last 30%."""
    if alpha <= 0.003 or p <= 0:
        return
    strokes, fills = _get(name)
    s = size / 100.0
    c.save()
    c.translate(cx - 50 * s, cy - 50 * s)
    c.scale(s, s)
    w = (width or max(2.6, size * 0.03)) / s
    sd = seed if seed is not None else (sum(map(ord, name)) % 50) + 3
    fa = clamp01((p - 0.7) / 0.3)
    if fa > 0:
        for path, acc in fills:
            c.drawPath(path, _paint_fill(accent if acc else color, 0.22 * alpha * fa))
            hatch(c, path, accent if acc else color, 0.75 * alpha * fa, 6.5, -40, 1.4 / s * 0.9, sd)
    lens = [skia.PathMeasure(q, False).getLength() or 1.0 for q in strokes]
    total = sum(lens)
    budget = total * clamp01(p / 0.8)
    for q, L in zip(strokes, lens):
        if budget <= 0:
            break
        if budget >= L:
            sketch(c, q, color, alpha, w, sd)
        else:
            m = skia.PathMeasure(q, False)
            seg = skia.Path()
            m.getSegment(0, budget, seg, True)
            sketch(c, seg, color, alpha, w, sd)
        budget -= L
    c.restore()


def _paint_fill(color, a):
    from .core import paint
    return paint(color, a)


def icon_in(c, name, cx, cy, size, t, t0, dur=0.9, color=INK, accent=MARKER, alpha=1.0, idle=True):
    """Time-driven: pops in (spring) while being drawn on over `dur` seconds, then idles with a tiny
    float + tilt so it never sits completely still."""
    if t < t0:
        return
    k = spring(t - t0, w=13, z=0.6)
    p = clamp01((t - t0) / dur)
    c.save()
    c.translate(cx, cy)
    if idle:
        c.translate(0, 3.5 * math.sin((t - t0) * 1.7 + cx * 0.01))
        c.rotate(2.2 * math.sin((t - t0) * 1.3 + cy * 0.01))
    sc = 0.7 + 0.3 * k
    c.scale(sc, sc)
    draw_icon(c, name, 0, 0, size, p, color, accent, alpha)
    c.restore()


ACCENTS = dict(yellow=MARKER, blue=BLUE, green=GREEN, orange=AMBER, red=RED, teal=CYAN)
