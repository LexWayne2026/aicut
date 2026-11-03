"""Reusable motion components in the whiteboard style. All are pure functions of time.

Annotations (rough-notation set, drawn on with progress p):
    annotate(c, kind, x, y, w, h, p, color)  kind: underline | highlight | box | circle | strike |
                                             crossed | bracket | squiggle
    annotate_text(c, kind, text, x, baseline, size, p, color, weight)  — wraps a word's bounds
Objects:
    stamp(c, text, cx, cy, t, t0)            slams in, ink burst, slight tilt
    sticky(c, text, cx, cy, t, t0, color)    sticky note that peels/flaps in
    counter(c, x, y, size, t, t0, t1, v0, v1, fmt)  rolling number with odometer blur
    bar_chart(c, x, y, w, h, values, labels, t, t0, colors)
    donut(c, cx, cy, r, fracs, colors, t, t0)
    line_chart(c, x, y, w, h, values, t, t0, color)
    progress_ring(c, cx, cy, r, frac, t, t0, color, label)
    callout(c, (ax, ay), (tx, ty), text, t, t0, color)   curved arrow from a point to a note
    checklist(c, x, y, items, times, t, size)  items tick off at given times
    typewriter(c, text, x, y, size, t, t0, cps)
    confetti(c, cx, cy, t, t0, n)            pencil confetti burst
    ambient(c, t, region, n, seed)           slow drifting doodles in empty margins
Transitions (Remotion TransitionSeries-style presentations, see wbx.scene):
    eraser_wipe / slide / iris / flip / page  + overlay "flash" at cut points
"""
import math
import random

import skia

from .core import (AMBER, BLUE, CYAN, GREEN, INK, MARKER, MUTE, PAPER, RED, EXPO_OUT, SMOOTH, _mix_white,
                   clamp01, doodle_circle, draw_text, ease_io, ease_out, hatch, layer, lerp, line_draw, marker,
                   paint, pscale, rrect, rrect_path, sketch, soft, sparkle, spring, squiggle, text_width)

# ====================================================================== annotations


def annotate(c, kind, x, y, w, h, p, color=RED, width=4.0, a=1.0, seed=7):
    """Hand-drawn annotation around/over the box (x, y, w, h), drawn on with progress p (0..1)."""
    p = clamp01(p)
    if p <= 0:
        return
    if kind == "underline":
        line_draw(c, [(x - 4, y + h + 6), (x + w + 6, y + h + 3)], p, color, a, width)
    elif kind == "squiggle":
        squiggle(c, x, x + w, y + h + 8, p, color, a, width, 6, 26, seed)
    elif kind == "highlight":
        marker(c, x - 8, y + h * 0.15, w + 16, h * 0.85, p, color if color != RED else MARKER, 0.6 * a)
    elif kind == "box":
        pts = [(x - 10, y - 8), (x + w + 10, y - 10), (x + w + 12, y + h + 8), (x - 8, y + h + 10), (x - 12, y - 6)]
        line_draw(c, pts, p, color, a, width)
    elif kind == "circle":
        doodle_circle(c, x + w / 2, y + h / 2, w / 2 + 22, h / 2 + 16, p, color, a, width, seed)
    elif kind == "strike":
        line_draw(c, [(x - 8, y + h * 0.55), (x + w + 8, y + h * 0.48)], p, color, a, width)
    elif kind == "crossed":
        line_draw(c, [(x - 6, y - 4), (x + w + 6, y + h + 4)], clamp01(p * 2), color, a, width)
        line_draw(c, [(x + w + 6, y - 4), (x - 6, y + h + 4)], clamp01(p * 2 - 1), color, a, width)
    elif kind == "bracket":
        d = 14
        line_draw(c, [(x - 4, y - 6), (x - 14, y - 6), (x - 14, y + h + 6), (x - 4, y + h + 6)],
                  clamp01(p * 2), color, a, width)
        line_draw(c, [(x + w + 4, y - 6), (x + w + 14, y - 6), (x + w + 14, y + h + 6), (x + w + 4, y + h + 6)],
                  clamp01(p * 2 - 1), color, a, width)


def annotate_text(c, kind, text, x, baseline, size, p, color=RED, weight=700, width=4.0, a=1.0, seed=7):
    """Annotate a word drawn with draw_text at (x, baseline)."""
    w = text_width(text, size, weight)
    annotate(c, kind, x, baseline - size * 0.82, w, size * 0.95, p, color, width, a, seed)
    return w


# ====================================================================== objects


def stamp(c, text, cx, cy, t, t0, color=RED, size=64, rot=-12, sub=None):
    """Rubber stamp: drops from big to size with a hard landing, ink splatter, then sits."""
    if t < t0:
        return
    dt = t - t0
    land = 0.18
    if dt < land:
        sc = pscale(EXPO_OUT(dt / land), 2.4, 1.0)
        a = clamp01(dt / land * 1.6)
    else:
        sc = 1 - 0.06 * math.exp(-(dt - land) * 14) * math.cos((dt - land) * 40)
        a = 1.0
    tw = text_width(text, size, 800)
    w, h = tw + size * 1.0, size * 1.55 + (size * 0.55 if sub else 0)
    c.save()
    c.translate(cx, cy)
    c.rotate(rot)
    c.scale(sc, sc)
    with layer(c, a * 0.92, 0, 1, 0, 0):
        sketch(c, rrect_path(-w / 2, -h / 2, w, h, 14), color, 1, 6, 31)
        sketch(c, rrect_path(-w / 2 + 9, -h / 2 + 9, w - 18, h - 18, 10), color, 0.8, 2.5, 32)
        draw_text(c, text, 0, size * 0.36 - (size * 0.25 if sub else 0), size, 800, color, "center")
        if sub:
            draw_text(c, sub, 0, size * 0.36 + size * 0.42, size * 0.38, 600, color, "center", tracking=0.12)
        # worn ink: knock a few holes out of the stamp
        rng = random.Random(len(text) * 13)
        for _ in range(16):
            px, py = rng.uniform(-w / 2, w / 2), rng.uniform(-h / 2, h / 2)
            hole = paint(PAPER, 0.55)
            c.drawCircle(px, py, rng.uniform(1.5, 4.5), hole)
    c.restore()
    if dt > land:
        k = clamp01((dt - land) / 0.35)
        rng = random.Random(7)
        for i in range(10):
            ang = rng.uniform(0, 2 * math.pi)
            r = (w * 0.55 + rng.uniform(0, 40)) * ease_out(k)
            c.drawCircle(cx + r * math.cos(ang), cy + r * math.sin(ang) * 0.6, rng.uniform(2, 5) * (1 - k * 0.6),
                         paint(color, 0.8 * (1 - k)))


def sticky(c, text, cx, cy, t, t0, color=MARKER, w=300, h=220, rot=-4, size=40, lines=None):
    """Sticky note slapped on the board: swings in around its top edge, then a tiny settle."""
    if t < t0:
        return
    k = spring(t - t0, w=10, z=0.55)
    ang = (1 - k) * 35 + rot
    c.save()
    c.translate(cx, cy - h / 2)
    c.rotate(ang)
    c.scale(1, 0.25 + 0.75 * clamp01(k * 1.3))
    x, y = -w / 2, 0
    c.drawRect(skia.Rect.MakeXYWH(x + 6, y + 10, w, h), paint("#5A6478", 0.18, blur=10))
    p = skia.Path()
    p.moveTo(x, y)
    p.lineTo(x + w, y)
    p.lineTo(x + w, y + h - 26)
    p.lineTo(x + w - 30, y + h)
    p.lineTo(x, y + h)
    p.close()
    c.drawPath(p, paint(_mix_white(color, 0.75), 1))
    sketch(c, p, INK, 0.45, 2, 61)
    fold = skia.Path()
    fold.moveTo(x + w, y + h - 26)
    fold.lineTo(x + w - 26, y + h - 22)
    fold.lineTo(x + w - 30, y + h)
    c.drawPath(fold, paint(_mix_white(color, 1.0), 0.6))
    for i, ln in enumerate(lines or [text]):
        draw_text(c, ln, x + 26, y + 70 + i * size * 1.3, size, 700, INK, t=t, t0=t0 + 0.25 + i * 0.2)
    c.restore()


def counter(c, x, y, size, t, t0, t1, v0, v1, fmt="{:.0f}", color=INK, align="left", weight=800, suffix=""):
    """Rolling number from v0 to v1 between t0 and t1 (EXPO_OUT), with a little vertical blur while fast."""
    p = (t - t0) / max(1e-6, t1 - t0)
    e = EXPO_OUT(p) if p < 1 else 1.0
    v = lerp(v0, v1, e) if p > 0 else v0
    speed = abs(EXPO_OUT(min(1, p + 0.02)) - e) if 0 < p < 1 else 0
    s = fmt.format(v) + suffix
    blur = min(6.0, speed * 400)
    return draw_text(c, s, x, y + (blur * 0.5), size, weight, color, align, blur_in=0, alpha=1.0) if blur < 0.3 else \
        _blurred_text(c, s, x, y, size, weight, color, align, blur)


def _blurred_text(c, s, x, y, size, weight, color, align, blur):
    p = skia.Paint()
    p.setImageFilter(skia.ImageFilters.Blur(0.1, blur))
    c.saveLayer(None, p)
    w = draw_text(c, s, x, y, size, weight, color, align)
    c.restore()
    return w


def bar_chart(c, x, y, w, h, values, labels, t, t0, colors=None, stagger=0.18, vmax=None, fmt="{:.0f}",
              value_size=34, label_size=32, unit=""):
    """Bars grow from the baseline one after another (EXPO_OUT), values count up, labels write in."""
    n = len(values)
    vmax = vmax or max(values) or 1
    colors = colors or [BLUE] * n
    gap = w / n
    bw = gap * 0.56
    line_draw(c, [(x - 10, y + h), (x + w + 10, y + h)], ease_io((t - t0 + 0.3) / 0.5), INK, 0.8, 3)
    for i, (v, lab) in enumerate(zip(values, labels)):
        ti = t0 + i * stagger
        g = EXPO_OUT((t - ti) / 0.9) if t > ti else 0
        bh = h * (v / vmax) * g
        bx = x + i * gap + (gap - bw) / 2
        if bh > 1:
            path = rrect_path(bx, y + h - bh, bw, bh, 8)
            c.drawPath(path, paint(colors[i], 0.22))
            hatch(c, path, colors[i], 0.85, 7, -45, 1.8, 11 + i)
            sketch(c, path, colors[i], 1, 2.6, 21 + i)
            draw_text(c, fmt.format(v * g) + unit, bx + bw / 2, y + h - bh - 16, value_size, 800, colors[i], "center")
        draw_text(c, lab, bx + bw / 2, y + h + label_size * 1.3, label_size, 600, INK, "center", t=t, t0=ti)


def donut(c, cx, cy, r, fracs, colors, t, t0, width=46, labels=None, label_size=30):
    """Segments sweep in one after another; hatch-filled ring."""
    start = -90.0
    for i, f in enumerate(fracs):
        ti = t0 + i * 0.25
        g = EXPO_OUT((t - ti) / 0.8) if t > ti else 0
        sweep = 360 * f * g
        if sweep > 0.5:
            outer = skia.Path()
            outer.addArc(skia.Rect.MakeXYWH(cx - r, cy - r, 2 * r, 2 * r), start, sweep)
            ring = skia.Path()
            ring.moveTo(cx + r * math.cos(math.radians(start)), cy + r * math.sin(math.radians(start)))
            ring.arcTo(skia.Rect.MakeXYWH(cx - r, cy - r, 2 * r, 2 * r), start, sweep, False)
            ri = r - width
            ring.arcTo(skia.Rect.MakeXYWH(cx - ri, cy - ri, 2 * ri, 2 * ri), start + sweep, -sweep, False)
            ring.close()
            c.drawPath(ring, paint(colors[i], 0.25))
            hatch(c, ring, colors[i], 0.9, 6, -40, 1.7, 30 + i)
            sketch(c, ring, colors[i], 1, 2.4, 40 + i)
            if labels and g > 0.9:
                mid = math.radians(start + sweep / 2)
                lx, ly = cx + (r + 50) * math.cos(mid), cy + (r + 50) * math.sin(mid)
                draw_text(c, labels[i], lx, ly + 10, label_size, 700, colors[i], "center", t=t, t0=ti + 0.6)
        start += 360 * f


def line_chart(c, x, y, w, h, values, t, t0, color=BLUE, dur=1.4, dots=True, vmax=None, vmin=None):
    vmax = vmax if vmax is not None else max(values)
    vmin = vmin if vmin is not None else min(values)
    pts = [(x + w * i / (len(values) - 1), y + h - h * (v - vmin) / max(1e-9, vmax - vmin)) for i, v in enumerate(values)]
    line_draw(c, [(x, y), (x, y + h), (x + w, y + h)], ease_io((t - t0) / 0.5), INK, 0.7, 3)
    p = ease_io((t - t0 - 0.3) / dur)
    line_draw(c, pts, p, color, 1, 5)
    if dots:
        for i, (px, py) in enumerate(pts):
            if p * (len(pts) - 1) >= i - 0.01:
                k = spring(t - t0 - 0.3 - dur * i / (len(pts) - 1), 15, 0.5)
                c.drawCircle(px, py, 9 * k, paint(color, 1))
                c.drawCircle(px, py, 4 * k, paint("#FFFFFF", 1))


def progress_ring(c, cx, cy, r, frac, t, t0, color=CYAN, label=None, size=56, width=16):
    sketch(c, _circle(cx, cy, r), INK, 0.15, width, 3)
    g = EXPO_OUT((t - t0) / 1.2) if t > t0 else 0
    if g > 0:
        arcp = skia.Path()
        arcp.addArc(skia.Rect.MakeXYWH(cx - r, cy - r, 2 * r, 2 * r), -90, 360 * frac * g)
        sketch(c, arcp, color, 1, width, 9)
    if label is not None:
        draw_text(c, label if isinstance(label, str) else f"{label * g:.0f}%", cx, cy + size * 0.36, size, 800,
                  INK, "center")


def _circle(cx, cy, r):
    p = skia.Path()
    p.addCircle(cx, cy, r)
    return p


def callout(c, anchor, at, text, t, t0, color=BLUE, size=36, bend=0.35):
    """Curved hand-drawn arrow from `at` (the note) to `anchor` (the thing), then the note writes in."""
    ax, ay = anchor
    tx, ty = at
    mx, my = (ax + tx) / 2, (ay + ty) / 2
    nx, ny = -(ay - ty), (ax - tx)
    ctrl = (mx + nx * bend, my + ny * bend)
    path = skia.Path()
    path.moveTo(tx, ty)
    path.quadTo(ctrl[0], ctrl[1], ax, ay)
    m = skia.PathMeasure(path, False)
    L = m.getLength()
    p = ease_io((t - t0) / 0.6)
    if p > 0:
        seg = skia.Path()
        m.getSegment(0, L * p, seg, True)
        sketch(c, seg, color, 1, 3.5, 13)
        if p >= 1:
            pos, tan = m.getPosTan(L)
            ang = math.atan2(tan.y(), tan.x())
            for s in (2.6, -2.6):
                line_draw(c, [(ax, ay), (ax - 18 * math.cos(ang + s / 5), ay - 18 * math.sin(ang + s / 5))], 1,
                          color, 1, 3.5)
    draw_text(c, text, tx, ty - 14, size, 700, color, "center", t=t, t0=t0 + 0.35)


def checklist(c, x, y, items, times, t, size=40, gap=1.6, color=GREEN):
    for i, (txt, ti) in enumerate(zip(items, times)):
        yy = y + i * size * gap
        k = spring(t - ti, 13, 0.6)
        if k <= 0.01:
            continue
        sketch(c, rrect_path(x, yy - size * 0.75, size * 0.85, size * 0.85, 6), INK, 0.7 * clamp01(k * 2), 2.4, 70 + i)
        from .core import check
        check(c, x + size * 0.45, yy - size * 0.35, size * 0.7, ease_out((t - ti - 0.15) / 0.35), color)
        draw_text(c, txt, x + size * 1.3, yy, size, 600, INK, t=t, t0=ti)


def typewriter(c, text, x, y, size, t, t0, cps=14, color=INK, weight=600, cursor=True):
    n = int(clamp01((t - t0) * cps / max(1, len(text))) * len(text)) if t > t0 else 0
    w = draw_text(c, text[:n], x, y, size, weight, color)
    if cursor and t > t0 and (n < len(text) or int(t * 2.5) % 2 == 0):
        c.drawRect(skia.Rect.MakeXYWH(x + w + 4, y - size * 0.8, 3, size * 0.95), paint(color, 0.8))
    return w


def confetti(c, cx, cy, t, t0, n=26, colors=(MARKER, BLUE, RED, GREEN, CYAN, AMBER), spread=420, seed=3):
    """Pencil confetti: little strokes, dots and stars fly out and fall with drag."""
    dt = t - t0
    if dt < 0 or dt > 2.6:
        return
    rng = random.Random(seed)
    fade = 1 - clamp01((dt - 1.8) / 0.8)
    for i in range(n):
        ang = rng.uniform(-math.pi * 0.95, -math.pi * 0.05)
        v = rng.uniform(0.5, 1.0) * spread
        drag = 1 - math.exp(-dt * 3.2)
        x = cx + math.cos(ang) * v * drag / 1.0
        y = cy + math.sin(ang) * v * drag + 160 * dt * dt
        col = colors[i % len(colors)]
        kind = i % 3
        rot = dt * rng.uniform(-400, 400)
        c.save()
        c.translate(x, y)
        c.rotate(rot)
        if kind == 0:
            line_draw(c, [(-9, 0), (9, 0)], 1, col, fade, 4)
        elif kind == 1:
            c.drawCircle(0, 0, 5, paint(col, fade))
        else:
            sparkle(c, 0, 0, 11, t, t0 + 0.05, col, fade)
        c.restore()


def ambient(c, t, region, n=12, seed=11, a=0.28):
    """Slow-drifting tiny doodles (stars, dots, plus signs, spirals) for empty board areas."""
    x0, y0, x1, y1 = region
    rng = random.Random(seed)
    for i in range(n):
        bx, by = rng.uniform(x0, x1), rng.uniform(y0, y1)
        sp = rng.uniform(0.15, 0.35)
        ph = rng.uniform(0, 6.28)
        x = bx + 14 * math.sin(t * sp + ph)
        y = by + 10 * math.cos(t * sp * 0.8 + ph)
        kind = i % 4
        col = (BLUE, MUTE, MARKER, CYAN)[i % 4]
        s = rng.uniform(7, 13)
        if kind == 0:
            line_draw(c, [(x - s, y), (x + s, y)], 1, col, a, 2.4)
            line_draw(c, [(x, y - s), (x, y + s)], 1, col, a, 2.4)
        elif kind == 1:
            c.drawCircle(x, y, s * 0.35, paint(col, a * 1.4))
        elif kind == 2:
            sparkle(c, x, y, s, t, -10, col, a * 1.6)
        else:
            p = skia.Path()
            for j in range(26):
                r = s * j / 26
                ang = j * 0.55 + t * sp
                (p.moveTo if j == 0 else p.lineTo)(x + r * math.cos(ang), y + r * math.sin(ang))
            sketch(c, p, col, a, 2, 90 + i)


# ====================================================================== transitions
# A scene can enter / exit with a presentation (wbx.scene applies them):
#   "blur" (default exit), "slide-left|right|up|down", "wipe" (whiteboard eraser), "iris", "flip", "page", "pop"
# and a cut-point overlay "flash" (a warm paper light-leak wash) without shortening the timeline.

ERASER_W, ERASER_H = 270, 110


def draw_eraser(c, x, y, rot=-8):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.drawRRect(rrect(-ERASER_W / 2 + 6, -ERASER_H / 2 + 10, ERASER_W, ERASER_H, 10), paint("#3A4250", 0.25, blur=10))
    felt = rrect_path(-ERASER_W / 2, ERASER_H * 0.1, ERASER_W, ERASER_H * 0.4, 6)
    body = rrect_path(-ERASER_W / 2, -ERASER_H / 2, ERASER_W, ERASER_H * 0.62, 10)
    c.drawPath(body, paint(BLUE, 0.9))
    c.drawPath(felt, paint("#D9D4C7", 1))
    hatch(c, felt, MUTE, 0.5, 5, 90, 1.2, 5)
    sketch(c, body, INK, 0.7, 2.4, 6)
    sketch(c, felt, INK, 0.6, 2, 7)
    draw_text(c, "ERASER", 0, -8, 30, 700, "#FFFFFF", "center", tracking=0.2)
    c.restore()


def presentation(c, kind, p, entering, box):
    """Apply a transition presentation to the canvas for progress p (0 = hidden, 1 = fully shown).
    Returns a callable to draw on top afterwards (e.g. the eraser) or None."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    q = 1 - p
    if kind.startswith("slide"):
        d = {"slide-left": (-1, 0), "slide-right": (1, 0), "slide-up": (0, -1), "slide-down": (0, 1)}[kind]
        s = 1 if entering else -1
        c.translate(-d[0] * w * q * s * 1.05, -d[1] * h * q * s * 1.05)
        return None
    if kind == "wipe":
        ex = lerp(x0 - 120, x1 + 120, 1 - p) if not entering else lerp(x1 + 120, x0 - 120, 1 - p)
        # the eraser sweeps left -> right: exiting content survives only ahead of it (to its right);
        # entering content is revealed behind it (to its left)
        if entering:
            ex = lerp(x0 - 160, x1 + 160, p)
            c.clipRect(skia.Rect.MakeLTRB(x0 - 400, y0 - 400, ex, y1 + 400))
        else:
            ex = lerp(x0 - 160, x1 + 160, 1 - p)
            c.clipRect(skia.Rect.MakeLTRB(ex, y0 - 400, x1 + 400, y1 + 400))
        ey = (y0 + y1) / 2 + 120 * math.sin((1 - p) * 9)
        return (lambda cc: draw_eraser(cc, ex, ey)) if 0.02 < p < 0.98 else None
    if kind == "iris":
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        r = math.hypot(w, h) / 2 * EXPO_OUT(p) if entering else math.hypot(w, h) / 2 * p
        path = skia.Path()
        path.addCircle(cx, cy, max(0.1, r))
        c.clipPath(path, doAntiAlias=True)
        return None
    if kind == "flip":
        cx = (x0 + x1) / 2
        c.translate(cx, 0)
        c.scale(max(0.02, math.cos((1 - p) * math.pi / 2)), 1)
        c.translate(-cx, 0)
        return None
    if kind == "page":
        c.translate(0, (1 - EXPO_OUT(p)) * h * (0.6 if entering else -0.6))
        c.rotate((1 - p) * (4 if entering else -4))
        return None
    if kind == "pop":
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        s = pscale(EXPO_OUT(p), 0.85, 1.0)
        c.translate(cx, cy)
        c.scale(s, s)
        c.translate(-cx, -cy)
        return None
    return None


def flash(c, t, t_cut, box, dur=0.7, color="#FFE7A8"):
    """Cut-point overlay: a warm, soft wash sweeping diagonally (paper 'light leak')."""
    p = (t - t_cut + dur / 2) / dur
    if not (0 < p < 1):
        return
    x0, y0, x1, y1 = box
    a = math.sin(math.pi * p) * 0.55
    cx = lerp(x0 - 300, x1 + 300, p)
    g = skia.Paint()
    g.setShader(skia.GradientShader.MakeRadial(skia.Point(cx, (y0 + y1) * 0.45), (x1 - x0) * 0.7,
                                               [skia.Color4f.FromColor(skia.Color(255, 231, 168, int(255 * a))).toColor(),
                                                skia.Color(255, 231, 168, 0)], [0, 1]))
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), g)
