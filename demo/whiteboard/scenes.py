"""Template 1 demo: the fish-oil demo script on the whiteboard. Every time comes from timeline.T (voice-over cues).

Layers: stage scenes sit on the board behind the taped presenter photo; "over" scenes are lower-third type on top
of the full-frame presenter. Design space 1080x1440: header x 64..760, y 64..260; content y 370..1250.
"""
import math
from types import SimpleNamespace

import skia

from wbx.components import ambient, confetti, counter, stamp
from wbx.core import (AMBER, BLUE, CYAN, GREEN, INK, MARKER, MUTE, RED, bottle, burst, clamp01, draw_label,  # noqa: F401
                      draw_text, ease_io, ease_out, form_icon, glass, hatch, layer, line_draw, marker, out_env, pencil,
                      pill, rrect, rrect_path, sketch, sparkle, spring, squiggle, tablet, text_width)
from wbx.core import paint as _paint
from wbx.icons import icon_in
from wbx.scene import frame

from timeline import DURATION, T as _T

T = SimpleNamespace(**_T)
X0, X1 = 64, 1016


def paint(color, a=1.0, stroke=None, blur=0.0):
    return pencil(color, a, stroke) if stroke else _paint(color, a, blur=blur)


def pbar(c, x, y, w, h, col, a=1.0):
    """Coloured-pencil bar: light wash + hatching + outline."""
    if a <= 0.003 or w <= 1:
        return
    path = rrect_path(x, y - 3, w, h + 6, (h + 6) / 2)
    c.drawPath(path, _paint(col, 0.22 * a))
    hatch(c, path, col, 0.9 * a, 5, -50, 1.8, int(x) % 13 + 2)
    sketch(c, path, col, a, 2.2, int(x) % 17 + 3)


def pop(t, t0, w=12, z=0.75):
    k = spring(t - t0, w, z)
    return k, clamp01(k * 1.5), 0.85 + 0.15 * k


def header(c, t, kicker, title, t0, t1=None, kc=BLUE):
    with frame(c):
        draw_label(c, kicker, X0, 118, 26, kc, t=t, t0=t0, t1=t1)
        draw_text(c, title, X0, 196, 64, 700, INK, t=t, t0=t0 + 0.08, t1=t1, stagger=0.04)


def title_over(c, t):
    t1 = T.super_ - 0.35
    oe = out_env(t, t1)
    draw_label(c, "FISH OIL  ·  鱼油", X0, 1080, 24, BLUE, t=t, t0=0.15, t1=t1)
    w0 = text_width("同样是", 110, 800)
    w = draw_text(c, "同样是鱼油", X0, 1200, 110, 800, INK, t=t, t0=0.05, stagger=0.07, t1=t1, style="bounce")
    squiggle(c, X0 + w0, X0 + w, 1236, ease_io((t - 0.75) / 0.6), MARKER, oe, 5, 8, 30)
    sparkle(c, X0 + w + 40, 1100, 24, t, 0.9, MARKER, oe)


def hook(c, t):
    header(c, t, "SAME FISH OIL", "同样是鱼油", T.super_ - 0.1)
    ambient(c, t, (40, 340, 1040, 520), n=8, seed=4, a=0.22)
    icon_in(c, "coins", 540, 640, 110, t, T.tens - 0.1, accent=GREEN)
    icon_in(c, "money_bag", 540, 500, 130, t, T.hundreds - 0.1, accent=AMBER)
    for cx, t0, col, lab, sub in ((300, T.super_, GREEN, "Ω-3", "鱼油 · 超市"), (780, T.imported, AMBER, "Ω-3", "鱼油 · 进口")):
        k, a, _ = pop(t, t0, 10, 0.78)
        bob = 4 * math.sin((t - t0) * 1.6)
        bottle(c, cx, 800 + (1 - k) * 120 + bob, 196, 300, col, lab, sub, alpha=a)
        c.drawOval(skia.Rect.MakeXYWH(cx - 110, 808, 220, 22), paint("#5A6478", 0.16 * a, blur=10))
    for t0, col, lab, val, frac, y in ((T.tens, GREEN, "超市", "几十块 / 瓶", 0.15, 950),
                                       (T.hundreds, AMBER, "进口", "好几百 / 瓶", 1.0, 1100)):
        k, a, _ = pop(t, t0 - 0.35)
        draw_text(c, lab, X0, y, 30, 600, col, t=t, t0=t0 - 0.35)
        g = spring(t - t0, 7, 0.95)
        c.drawRRect(rrect(X0, y + 22, X1 - X0, 16, 8), paint(INK, 0.06 * a))
        if g > 0:
            pbar(c, X0, y + 22, max(16, (X1 - X0) * frac * g), 16, col, 0.95 * a)
        draw_text(c, val, X1, y, 34, 700, INK, "right", t=t, t0=t0 + 0.15)
    burst(c, X1 - 40, 1060, 40, 90, 7, t, T.hundreds + 0.2, AMBER, 1, 4)


def dose(c, t):
    header(c, t, "OMEGA-3 PER CAPSULE", "一粒含有多少", T.dose)
    pill(c, 540, 440, "每天想补充 900 mg", 30, CYAN, t=t, t0=T.d900)

    def row(y, col, lab, sub, t_lab, slot_ts, mult, t_mult, per):
        draw_text(c, lab, X0, y, 36, 800, col, t=t, t0=t_lab)
        draw_text(c, sub, X0 + text_width(lab, 36, 800) + 20, y, 30, 500, MUTE, t=t, t0=t_lab + 0.15)
        ty = y + 100
        for i, ts in enumerate(slot_ts):
            x = 118 + i * 136
            k, a, s = pop(t, ts, 14, 0.6)
            if a > 0:
                tablet(c, x, ty - (1 - k) * 40, 46 * (0.6 + 0.4 * k), alpha=a)
                draw_text(c, per, x, ty + 78, 22, 600, MUTE, "center", family="inter", alpha=a)
        draw_text(c, mult, X1, ty + 22, 64, 800, col, "right", t=t, t0=t_mult, family="sc")
        by = ty + 116                           # 0..900 mg bar in three 300 mg segments
        c.drawRRect(rrect(X0, by, X1 - X0, 14, 7), paint(INK, 0.07))
        for i in (1, 2):
            xx = X0 + (X1 - X0) * i / 3
            c.drawLine(xx, by - 4, xx, by + 18, paint(INK, 0.18, stroke=1.5))
        seg = (X1 - X0) / len(slot_ts)
        for i, ft in enumerate(slot_ts):
            g = spring(t - ft, 10, 0.9)
            if g > 0:
                pbar(c, X0 + i * seg + 2, by, max(10, (seg - 4) * g), 14, col, 0.95)

    if t > T.d300:
        if t < T.three - 0.6:
            draw_text(c, "累计 300 mg", X1, 520, 32, 700, GREEN, "right")
        else:
            counter(c, X1, 520, 32, t, T.three - 0.6, T.three + 0.3, 300, 900, "累计 {:.0f} mg", GREEN, "right", 700)
    three = [T.d300] + [T.three - 0.4 + i * 0.2 for i in (1, 2)]
    row(520, GREEN, "普通", "一粒 300 mg", T.d300 - 0.5, three, "× 3 粒", T.three, "300")
    row(880, AMBER, "高浓度", "可能一粒就够", T.conc - 0.3, [T.one - 0.2], "× 1 粒", T.one, "900")
    stamp(c, "一粒就够", 520, 975, t, T.one + 0.25, AMBER, 46, -8)


def check_over(c, t):
    draw_label(c, "THE ORDER  ·  先后", X0, 1040, 24, BLUE, t=t, t0=T.check)
    w1 = text_width("先看含量", 104, 800)
    marker(c, X0 - 10, 1118, w1 + 24, 52, ease_out((t - T.check - 0.7) / 0.6))
    draw_text(c, "先看含量", X0, 1172, 104, 800, INK, t=t, t0=T.check, stagger=0.07, style="bounce")
    w2 = draw_text(c, "再看价格", X0, 1290, 72, 700, MUTE, t=t, t0=T.price, stagger=0.06)
    squiggle(c, X0, X0 + w2, 1316, ease_io((t - T.price - 0.6) / 0.6), CYAN, 1, 5, 8, 34)
    sparkle(c, X0 + w1 + 50, 1120, 24, t, T.check + 0.9)


FORMS = (("sr", "软胶囊", "SOFTGEL", "f_soft"), ("plain", "小粒胶囊", "MINI", "f_mini"),
         ("coated", "肠溶胶囊", "ENTERIC", "f_enteric"), ("lipo", "乳液", "EMULSION", "f_emul"),
         ("gummy", "软糖", "GUMMY", "f_gummy"), ("liquid", "液体", "LIQUID", "f_liquid"))


def forms(c, t):
    header(c, t, "SAME FISH OIL, MANY FORMS", "可以做成", T.forms)
    tw, th, gap = 296, 300, 24
    for i, (kind, zh, en, key) in enumerate(FORMS):
        t0 = getattr(T, key)
        k, a, s = pop(t, t0, 12, 0.72)
        x, y = 72 + (i % 3) * (tw + gap), 390 + (i // 3) * (th + gap)
        fl = clamp01((t - t0) / 0.45)                      # cards flip in
        c.save()
        c.translate(x + tw / 2, 0)
        c.scale(max(0.02, math.sin(fl * math.pi / 2)), 1)
        c.translate(-(x + tw / 2), 0)
        with layer(c, a, (1 - clamp01(k)) * 6, s, x + tw / 2, y + th / 2, dy=(1 - k) * 30):
            glass(c, x, y, tw, th, 36)
            form_icon(c, kind, x + tw / 2, y + 128, 82, t, INK)
            draw_text(c, zh, x + tw / 2, y + 242, 40, 700, INK, "center")
            draw_text(c, en, x + tw / 2, y + 278, 21, 600, MUTE, "center", family="inter", tracking=0.14)
        c.restore()
    pill(c, X0, 1110, "选一种", 40, BLUE, t=t, t0=T.pick, align="left")
    w = draw_text(c, "你吃得下去的", X0 + 170, 1126, 56, 800, INK, t=t, t0=T.pick + 0.3, stagger=0.05, style="bounce")
    squiggle(c, X0 + 170, X0 + 170 + w, 1150, ease_io((t - T.pick - 0.9) / 0.6), MARKER, 1, 5, 8, 30)


def outro_over(c, t):
    w = draw_text(c, "下期聊", X0, 1110, 56, 600, MUTE, t=t, t0=T.outro + 0.4)
    w1 = text_width("怎么看标签", 104, 800)
    marker(c, X0 - 10, 1160, w1 + 24, 52, ease_out((t - T.outro - 1.0) / 0.6))
    draw_text(c, "怎么看标签", X0, 1214, 104, 800, INK, t=t, t0=T.outro + 0.6, stagger=0.07, style="bounce")
    confetti(c, X0 + w1 * 0.6, 1140, t, T.outro + 1.4, n=30, spread=520)
    icon_in(c, "magnifier", X0 + w1 + 110, 1170, 120, t, T.outro + 1.0, accent=MARKER)


SCENES = [
    dict(t0=0.0, t1=T.super_ - 0.35, layer="over", fn=title_over, exit=None),
    dict(t0=T.super_ - 0.3, t1=T.dose - 0.2, fn=hook, enter="pop"),
    dict(t0=T.dose - 0.2, t1=T.check - 0.2, fn=dose, enter="slide-left", flash=True),
    dict(t0=T.check - 0.2, t1=T.forms - 0.3, layer="over", fn=check_over),
    dict(t0=T.forms - 0.3, t1=T.outro - 0.3, fn=forms, enter="page"),
    dict(t0=T.outro - 0.3, t1=DURATION + 5, layer="over", fn=outro_over),
]
