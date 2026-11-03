"""Template 3 demo: three passages of the fish-oil demo script built as Soft Glass scenes. Between passages the
presenter stays full frame with captions. Copy these patterns: few cards, glass over video, every beat on a word cue."""
from wbx.softglass import (ACCENT, G1, G2, MUTE, NAVY, SOFTS, WHITE, around, bar, button, card, chevrons, digit_w,  # noqa: F401
                           fade_out, glass, glass_pill, glyph, grad, lin, orb, outline, pop, pulse, ripple, rise, roll, slide, spring,
                           stroke, text, text_w, fill, rrect)
from wbx.cues import at

from timeline import FORM_CUES, T


# ------------------------------------------------------------------ hook: full-frame presenter with two glass rows
def glass_row(c, y, pair, kind, title, t, t_val, val, k=1.0):
    x, w, h = 90, 900, 128
    glass(c, x, y, w, h, h / 2, ta=.16, blur=26)
    orb(c, x + 66, y + h / 2, 42, pair, kind)
    text(c, title, x + 132, y + h / 2 + 15, 42, WHITE)
    pop(c, t, t_val, x + w - 110, y + h / 2, lambda: (c.save(), around(c, x + w - 110, y + h / 2, k, k),
                                                     text(c, val, x + w - 44, y + h / 2 + 15, 42, WHITE, "r", "m"), c.restore()))


def scene_hook(c, t):
    s = "同样是鱼油"
    for i, ch in enumerate(s):
        x0 = 540 - text_w(s, 100) / 2 + text_w(s[:i], 100)
        rise(c, t, .05 + i * .06, x0 + 50, 880, lambda ch=ch, x0=x0: text(c, ch, x0, 920, 100, WHITE), dy=60, w=15, z=.5)
    t_otc, t_few = at("超市里的", "超市"), at("超市里的", "几十")
    t_imp, t_100 = at("而进口的一瓶", "进口"), at("而进口的一瓶", "好几百")
    rise(c, t, t_otc - .05, 540, 1060, lambda: glass_row(c, 996, SOFTS[0], "capsule", "超市", t, t_few, "几十块"))
    k = pulse(t, t_100, .16)
    rise(c, t, t_imp - .05, 540, 1210, lambda: glass_row(c, 1146, SOFTS[1], "bottle", "进口", t, t_100 - .12, "好几百", k))
    ripple(c, 880, 1210, t, t_100, WHITE, 60, 240, .6)


# ------------------------------------------------------------------ dose: gradient number + hero video, then the bar chart
def scene_dose(c, t):
    t0, tB = T["dose"], T["chart"]
    t_one, t_100 = at("普通的一粒含有", "一"), at("普通的一粒含有", "300")
    t_need, t_500, t_vc = at("如果每天想补充", "如果"), at("如果每天想补充", "900"), at("普通的一粒含有", "Omega")
    t_five, t_1 = at("普通的就要吃三粒", "三"), at("高浓度的可能", "一")
    q = slide(t, tB, 10, .62)

    # side cards peek from behind the hero video, then slide off for the chart
    for side, x, pair, kind in ((-1, 96, SOFTS[1], "capsule"), (1, 824, SOFTS[2], "bottle")):
        def peek(x=x, pair=pair, kind=kind, side=side):
            c.drawRRect(rrect(x, 500, 160, 480, 60), grad(x, 500, x + 160, 980, *pair))
            glyph(c, kind, x + 80 - side * 10, 740, 110, WHITE)
        c.save()
        c.translate(side * 260 * q, 0)
        fade_out(c, t, tB, x + 80, 740, lambda peek=peek, x=x: rise(c, t, t0 + .35, x + 80, 740, peek, dy=60), dur=.35)
        c.restore()

    # headline: label, gradient odometer, unit; it shrinks up beside the avatar for the chart
    c.save()
    around(c, 540, 250, 1 - .38 * q, 1 - .38 * q, dx=96 * q, dy=-96 * q)
    label = "普通的一粒含有" if t < t_need else "如果每天想补充"
    if t > t_one:
        rise(c, t, t_one if t < t_need else t_need, 540, 150, lambda: text(c, label, 540, 170, 40, MUTE, "c", "m"), dy=24, blur=8)
    if t > t_100:
        unit = "毫克" if t < t_vc or t > t_need else "毫克 Omega-3"
        x0 = 540 - (digit_w(190) * 3 + 24 + text_w(unit, 56)) / 2
        gp = grad(x0, 200, x0 + 340, 340)

        def num():
            if t < t_500:
                roll(c, None, "300", x0, 340, 190, gp, t, t_100)
            else:
                roll(c, "300", "900", x0, 340, 190, gp, t, t_500, w=9, z=.45)
            text(c, unit, x0 + digit_w(190) * 3 + 24, 334, 56, NAVY)
        rise(c, t, t_100, 540, 280, num, dy=40, blur=10)
    c.restore()

    # the chart card: how many tablets
    def chart():
        card(c, 66, 330, 948, 880, 64)
        text(c, "每天 900 毫克，要吃几粒", 540, 432, 42, NAVY, "c")
        chevrons(c, 118, 962, 418)
        for cx, n, tf, lab, sub, hot in ((380, 3, t_five, "普通", "一粒 300 毫克", False), (700, 1, t_1, "高浓度", "可能一粒就够", True)):
            top, bot, bw = 500, 1060, 176
            hgt = (n * 88 + 40) * slide(t, tf, 9, .5)
            bar(c, cx, top, bot, bw, hgt, hot)
            for i in range(n):
                yy = bot - 64 - i * 88
                if t > tf and yy > bot - hgt + 40:
                    pop(c, t, tf + .1 + i * .07, cx, yy, lambda yy=yy, cx=cx: (c.drawCircle(cx, yy, 34, fill(WHITE, .92)),
                                                                              glyph(c, "capsule", cx, yy, 86, ACCENT if hot else "#9C98E6", line=True)))
            if t > tf:
                vy = bot - hgt - 30
                rise(c, t, tf + .1, cx, vy, lambda cx=cx, vy=vy, n=n: text(c, f"{n} 粒", cx, vy, 52, NAVY, "c"), dy=20, blur=6)
            text(c, lab, cx, 1116, 38, NAVY, "c")
            text(c, sub, cx, 1162, 28, MUTE, "c", "m", 0)
    rise(c, t, tB + .12, 540, 770, chart, dy=110, s0=.9)


def dose_over(c, t):
    """Glass on top of the hero video: the corner arrow and the label that follows the speech."""
    t0, tB = T["dose"], T["chart"]
    t_100, t_500 = at("普通的一粒含有", "300"), at("如果每天想补充", "900")

    def on_video():
        rise(c, t, t0 + .5, 738, 478, lambda: (glass(c, 706, 446, 64, 64, 32, ta=.2), glyph(c, "up", 738, 478, 80, WHITE)), dy=20)
        if t < t_500 + .25:
            pop(c, t, t_100 + .25, 540, 990, lambda: glass_pill(c, 540, 990, "一粒 300 毫克"))
        else:
            pop(c, t, t_500 + .25, 540, 990, lambda: glass_pill(c, 540, 990, "每天 900 毫克"))
    fade_out(c, t, tB, 540, 990, on_video)


# ------------------------------------------------------------------ dosage forms: heading, option tiles, gradient button
ITEMS = FORM_CUES
TW, TH, TG, TX, TY = 290, 224, 22, 83, 590


def tile_xy(i):
    return TX + (i % 3) * (TW + TG), TY + (i // 3) * (TH + TG)


def scene_forms(c, t):
    t0, t_move = T["forms"], T["move"]
    times = [at(*cue, after=t0) for _, cue, _ in ITEMS]
    rise(c, t, t0 + .1, 948, 170, lambda: (glass(c, 884, 106, 128, 128, 64, ta=.45), text(c, "02", 948, 186, 46, NAVY, "c")), dy=30)
    rise(c, t, t_move + .2, 400, 150, lambda: (text(c, "再看剂型", 270, 156, 32, MUTE, wt="m"), text(c, "选吃得下去的", 270, 210, 44, NAVY)), dy=30)
    for j, (line, y) in enumerate((("同样的鱼油", 404), ("可以做成", 510))):
        rise(c, t, t_move + .3 + j * .12, 540, y - 40, lambda line=line, y=y: text(c, line, 540, y, 92, NAVY, "c"), dy=50, w=14)

    cur = -1
    for i, ((name, _, kind), ti) in enumerate(zip(ITEMS, times)):
        x, y = tile_xy(i)
        if t > ti:
            cur = i

        def one(x=x, y=y, i=i, name=name, kind=kind, ti=ti):
            card(c, x, y, TW, TH, 48)
            k = pulse(t, ti + .2, .12)
            pop(c, t, ti + .08, x + TW / 2, y + 92, lambda: (c.save(), around(c, x + TW / 2, y + 92, k, k),
                                                           orb(c, x + TW / 2, y + 92, 54, SOFTS[i], kind), c.restore()))
            rise(c, t, ti + .16, x + TW / 2, y + 180, lambda: text(c, name, x + TW / 2, y + 190, 36, NAVY, "c", "m"), dy=16, blur=6)
        rise(c, t, ti, x + TW / 2, y + TH / 2, one, dy=80, s0=.82)
    if cur >= 0:                            # gradient selection ring springs to the form being named
        q = slide(t, times[cur], 14, .6)
        (px, py), (nx, ny) = tile_xy(max(cur - 1, 0)), tile_xy(cur)
        rx, ry = px + (nx - px) * q, py + (ny - py) * q
        outline(c, rx - 3, ry - 3, TW + 6, TH + 6, 51)

    n = sum(1 for ti in times if t > ti)

    def counter():
        button(c, 90, 1100, 900, 120)
        x0 = 540 - (digit_w(52) + 14 + text_w("种剂型", 44)) / 2
        roll(c, str(n - 1) if n > 1 else None, str(max(n, 1)), x0, 1176, 52, fill(WHITE), t, times[max(n - 1, 0)], w=16, z=.5)
        text(c, "种剂型", x0 + digit_w(52) + 14, 1175, 44, WHITE)
    rise(c, t, times[0], 540, 1160, counter, dy=60)


SCENES = [
    dict(t0=0.0, t1=T["hook_end"], layer="over", fn=scene_hook),
    dict(t0=T["dose"], t1=T["dose_end"], fn=scene_dose),
    dict(t0=T["dose"], t1=T["dose_end"], layer="over", fn=dose_over),
    dict(t0=T["forms"], t1=T["forms_end"], fn=scene_forms),
]
