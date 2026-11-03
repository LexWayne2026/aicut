"""Template 2 demo: three passages of the fish-oil demo script built as Pop Card scenes. Between passages the
presenter stays full frame with captions. Copy these patterns: every beat on a word cue, one motion verb per element."""
import math

import skia

from wbx.popcard import (LW, INK, LIME, MUTE, ORANGE, PINK, WHITE, YELLOW, around, back_out, badge, bottle, burst, capsule,  # noqa: F401
                         card, coated, dome, drop, drop_text, dropper, fill, stroke, gummy, idle, liposome, m_drop, pill, pop, pulse, rays,
                         spring, star, tablet, text, whip)
from wbx.cues import at

from timeline import T


def softgel(c, cx, cy, r, color=YELLOW, rot=-18):
    """A fish-oil softgel: inked golden oval with a highlight."""
    c.save()
    c.translate(cx, cy)
    c.rotate(rot)
    oval = skia.Rect.MakeXYWH(-r, -r * .62, 2 * r, r * 1.24)
    c.drawOval(oval, fill(color))
    c.drawOval(oval, stroke(INK, LW))
    c.drawLine(-r * .55, -r * .28, -r * .1, -r * .36, stroke(WHITE, 8, .85))
    c.restore()


def scene_hook(c, t):
    drop_text(c, "同样是鱼油", 540, 1040, 112, WHITE, t, .05, align="c", stag=.05, fall=240)
    pop(c, t, .55, 980, 930, lambda: star(c, 980, 930, 40, YELLOW), spin=180)
    pop(c, t, .7, 92, 960, lambda: star(c, 92, 960, 24, LIME), spin=-180)
    t_otc, t_few = at("超市里的", "超市"), at("超市里的", "几十")
    t_imp, t_100 = at("而进口的一瓶", "进口"), at("而进口的一瓶", "好几百")
    iy, ir = idle(t, 1)
    whip(c, t, t_otc - .1, 180, 1216, lambda: bottle(c, 180, 1216 + iy, .92, LIME, "超市", rot=-9 + ir, sticker=True), sign=-1)
    pop(c, t, t_few, 410, 1176, lambda: pill(c, 300, 1176, "几十块一瓶", 56, LIME, INK, rot=-2.5, shadow=INK))
    iy, ir = idle(t, 3)
    whip(c, t, t_imp - .1, 900, 1216, lambda: bottle(c, 900, 1216 + iy, .92, ORANGE, "进口", rot=9 + ir, sticker=True), sign=1)
    t_bottle, k = at("而进口的一瓶", "一瓶"), pulse(t, t_100, .28)
    pop(c, t, t_bottle, 620, 1298, lambda: (c.save(), around(c, 620, 1298, k, k), pill(c, 780, 1298, "一瓶好几百", 56, PINK, WHITE, "r", rot=2, shadow=INK), c.restore()))
    burst(c, 620, 1298, t, t_100, YELLOW, r0=120, r1=300)


def scene_dose(c, t):
    t0 = T["dose"]
    t_100 = at("普通的一粒含有", "300")
    t_need, t_500 = at("如果每天想补充"), at("如果每天想补充", "900")

    # top: 300 mg beside the presenter on the left; when the presenter swaps sides, the number slides over and becomes 900 mg
    q = spring(t - t_need, 10, .52)
    dx = 344 * (1 - q)
    back_out(c, t, t_need - .1, 400, 100, lambda: pop(c, t, t0 + .25, 400, 100, lambda: text(c, "普通一粒", 400, 130, 56, WHITE)))
    back_out(c, t, t_500 - .2, 200 + dx, 300, lambda: pop(c, t, t_100, 200 + dx, 300, lambda: text(c, "300", 56 + dx, 348, 236, WHITE, track=-.04)))
    back_out(c, t, t_500 - .2, 150 + dx, 420, lambda: whip(c, t, t_100 + .12, 150 + dx, 420, lambda: text(c, "毫克", 66 + dx, 422, 64, INK), sign=-1))
    drop_text(c, "如果每天想补充", 66, 130, 56, WHITE, t, t_need, stag=.035, fall=120)
    pop(c, t, t_500, 220, 280, lambda: text(c, "900", 56, 348, 236, WHITE, track=-.04), w=19, z=.3)
    burst(c, 240, 270, t, t_500, YELLOW, r0=130, r1=340, n=12)
    whip(c, t, t_500 + .22, 250, 420, lambda: text(c, "毫克 Omega-3", 66, 440, 64, INK), sign=-1)

    # white dome rises with a bounce
    sheet = spring(t - t0, 10, .46)
    y = 520 + (1 - sheet) * 1040
    dome(c, y, bulge=80 + 50 * (1 - sheet))
    pop(c, t, t0 + .32, 540, 500, lambda: badge(c, 540, 500, 112, "2"), spin=-90)

    pop(c, t, t0 + .4, 130, 660, lambda: pill(c, 72, 660, "普通", 44, LIME, INK, padx=28, pady=14))
    drop_text(c, "一粒 300 毫克", 252, 676, 48, MUTE, t, t0 + .55, stag=.03, fall=60)

    t_five = at("普通的就要吃三粒", "三粒")
    t_need5 = at("普通的就要吃三粒", "要")
    drop_text(c, "要吃三粒", 72, 796, 88, INK, t, t_need5, stag=.045, fall=130)
    # the first capsule holds centre stage at full size, then flies into the row when the other four arrive
    q = spring(t - t_need5, 12, .5)
    hx, hr = 540 + (136 - 540) * q, 170 + (77 - 170) * q
    iy, ir = idle(t, 4, 7 * (1 - min(q, 1)))
    pop(c, t, t_100, hx, 900, lambda: softgel(c, hx, 900 + 30 * q + iy, hr, rot=-20 + ir * 3 + q * 8), w=15, z=.33, spin=-60)
    if q < .5:
        pop(c, t, t_100 + .12, hx, 1120, lambda: text(c, "300 毫克", hx, 1136, 60, MUTE, "c"), w=20)
    elif t > t_100:
        pop(c, t, t_need5 + .05, 136, 1034, lambda: text(c, "300", 136, 1044, 34, MUTE, "c"), w=20)
    for i in range(1, 3):
        x = 136 + i * 202
        ti = t_five + (i - 1) * .09
        wave = -24 * math.exp(-5 * max(0, t - t_five - .55)) * math.sin(max(0, t - t_five - .55 - i * .05) * 14) if t > t_five + .55 + i * .05 else 0
        pop(c, t, ti, x, 930, lambda: softgel(c, x, 930 + wave, 74 + 4 * math.sin(i * 2), rot=-20 + i * 11 + wave * .6))
        pop(c, t, ti + .08, x, 1034, lambda: text(c, "300", x, 1044, 34, MUTE, "c"), w=20)

    t_imp, t_one = at("高浓度的可能", "高浓度"), at("高浓度的可能", "一粒")
    if t > t_imp - .15:
        p = spring(t - t_imp + .15, 12, .8)
        c.drawLine(72, 1090, 72 + 936 * min(p, 1), 1090, stroke("#E6E6EC", 5))
    pop(c, t, t_imp, 130, 1160, lambda: pill(c, 72, 1160, "高浓度", 44, ORANGE, INK, padx=28, pady=14))
    drop_text(c, "可能", 72, 1270, 52, MUTE, t, t_imp + .35, stag=.03, fall=70)
    drop_text(c, "一粒就够", 196, 1270, 88, INK, t, t_one - .18, stag=.06, fall=130)
    dt = t - (t_one - .3)
    if dt > 0:                                # the single capsule falls in from above and bounces on the line
        v = m_drop(dt)
        c.save()
        around(c, 860, 1274, v["sx"], v["sy"], dy=(drop(dt) - 1) * 480)
        softgel(c, 860, 1178, 96, ORANGE, rot=-18 + (1 - drop(dt)) * 180)
        c.restore()
    burst(c, 860, 1200, t, t_one, PINK, r0=110, r1=260)


ITEMS = [("软胶囊", ("可以做成软胶囊", "软胶囊"), lambda c, x, y: softgel(c, x, y, 78)),
         ("小粒胶囊", ("小粒胶囊",), lambda c, x, y: capsule(c, x, y, .62, PINK, WHITE, dots=True)),
         ("肠溶胶囊", ("肠溶胶囊",), lambda c, x, y: coated(c, x, y, .92)),
         ("乳液", ("乳液",), lambda c, x, y: liposome(c, x, y, .78)),
         ("软糖", ("软糖或者是液体", "软糖"), lambda c, x, y: gummy(c, x, y + 4, .68)),
         ("液体", ("软糖或者是液体", "液体"), lambda c, x, y: dropper(c, x, y + 4, .68))]


def scene_forms(c, t):
    t0 = T["forms"]
    c.save()
    around(c, 540, 760, rot=(t - t0) * 7)
    rays(c, 540, 760, "#FFF04D")
    c.restore()
    pop(c, t, t0 + .1, 118, 130, lambda: badge(c, 118, 130, 96, "2"), spin=-90)
    whip(c, t, t0 + .1, 260, 130, lambda: text(c, "再看剂型", 188, 150, 60), sign=-1)
    drop_text(c, "选吃得下去的", 66, 322, 128, INK, t, t0 + .2, stag=.045, fall=210, track=-.03)
    tilts = [-2.5, 2, -1.5, 2, -2, 2.5]
    cw, ch, gap = 300, 282, 24
    for i, (name, cue, fn) in enumerate(ITEMS):
        ti = at(*cue, after=t0)
        x = 66 + (i % 3) * (cw + gap)
        y = 400 + (i // 3) * (ch + gap)

        def one(x=x, y=y, i=i, ti=ti, name=name, fn=fn):
            done = card(c, x, y, cw, ch, r=52, rot=tilts[i], shadow="#9A6B00", sa=.42)
            iy, ir = idle(t, i, 4)
            pop(c, t, ti + .08, cw / 2, 122, lambda: (c.save(), around(c, cw / 2, 122, rot=ir * 3, dy=iy), fn(c, cw / 2, 122), c.restore()), w=15, z=.33, spin=-40)
            pop(c, t, ti + .16, cw / 2, 240, lambda: text(c, name, cw / 2, 254, 46, INK, "c"), w=20)
            done()
        cx, cy = x + cw / 2, y + ch / 2
        pop(c, t, ti, cx, cy, one, w=16, z=.34, spin=(-1) ** i * 22)
    t_move = T["move"]
    drop_text(c, "同样的鱼油", 318, 1130, 84, INK, t, t_move + .2, stag=.04, fall=100)
    drop_text(c, "可以做成", 318, 1228, 60, INK, t, t_move + .5, stag=.04, fall=90)


SCENES = [
    dict(t0=0.0, t1=T["hook_end"], layer="over", fn=scene_hook),
    dict(t0=T["dose"], t1=T["dose_end"], bg=PINK, fn=scene_dose),
    dict(t0=T["forms"], t1=T["forms_end"], bg=YELLOW, enter="slam", fn=scene_forms),
]
