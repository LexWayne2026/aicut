"""Build the public demo: a drawn stand-in presenter clip and a timed transcript, copied into the three demo
projects (whiteboard, popcard, softglass). No real footage or speech is involved, so anyone can render it.

    python demo/make_demo.py
    python wbx/render.py --project demo/softglass --preview
"""
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import skia

DEMO = Path(__file__).resolve().parent
W, H, FPS = 1080, 1440, 30
CPS = 4.6                                  # spoken characters per second
PUNCT = "，。、！？,.!?"

# (pause before the line, Chinese, English). The pauses leave room for scene changes.
SCRIPT = [
    (.3, "同样是鱼油，", "Both are fish oil,"),
    (.25, "超市里的几十块一瓶，", "the supermarket one is a few dozen yuan a bottle,"),
    (.3, "而进口的一瓶要好几百。", "while an imported bottle costs several hundred."),
    (.9, "普通的一粒含有300毫克Omega-3，", "a regular capsule holds 300 mg of Omega-3,"),
    (.35, "如果每天想补充900毫克，", "if you want 900 mg a day,"),
    (.35, "普通的就要吃三粒，", "you need three regular capsules,"),
    (.3, "高浓度的可能一粒就够。", "a concentrated one may be enough."),
    (.6, "所以先看含量，再看价格。", "So check the dose first, then the price."),
    (.9, "同样的鱼油，", "The same fish oil"),
    (.25, "可以做成软胶囊、小粒胶囊、肠溶胶囊，", "comes as softgels, mini capsules, enteric capsules,"),
    (.2, "还有乳液、软糖或者是液体，", "emulsions, gummies or liquid,"),
    (.4, "选一种你吃得下去的。", "pick the one you will actually take."),
    (.7, "关注我，下期聊怎么看标签。", "Follow for how to read the label next time."),
]


def captions():
    out, t = [], 0.0
    for i, (gap, zh, en) in enumerate(SCRIPT):
        t += gap
        t0, units = t, []
        for ch in zh:
            if ch in PUNCT and units:
                units[-1]["text"] += ch
                continue
            units.append(dict(text=ch, start=round(t, 3), end=round(t + 1 / CPS, 3)))
            t += 1 / CPS
        out.append(dict(id=f"c{i:03d}", t0=round(t0, 3), t1=round(t, 3), zh=zh, en=en,
                        highlight=dict(source="demo-script", language="zh", units=units)))
    return out


def talking(caps, t):
    """Mouth opening 0..1 while a line is spoken."""
    for ln in caps:
        if ln["t0"] <= t < ln["t1"]:
            return .35 + .65 * abs(math.sin(t * 15.3)) * (.6 + .4 * math.sin(t * 4.1))
    return 0.0


def paint(color, a=1.0, blur=0):
    p = skia.Paint(AntiAlias=True, Color=skia.Color4f(skia.Color(*color)).makeOpaque().toColor())
    p.setAlphaf(a)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def presenter(c, t, caps):
    """A flat illustrated host in a warm studio: breathing, blinking, head sway and a talking mouth."""
    bg = skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 0), (0, H)], [skia.Color(*rgb("#EFE7DC")), skia.Color(*rgb("#D8CDBF"))]))
    c.drawRect(skia.Rect.MakeWH(W, H), bg)
    c.drawCircle(880, 260, 260, paint(rgb("#FFF6E3"), .8, 90))                 # lamp glow
    for dx, dy, r in ((140, 1000, 120), (210, 900, 95), (90, 880, 80), (180, 800, 70)):   # soft plant
        c.drawCircle(dx, dy, r, paint(rgb("#8FA88A"), .55, 30))
    c.drawRoundRect(skia.Rect.MakeXYWH(95, 1040, 150, 230), 26, 26, paint(rgb("#B9876A"), .7, 12))

    breath = math.sin(t * 1.6) * 4
    sway = math.sin(t * 1.1) * 2.2 + math.sin(t * 2.7) * .8
    # body
    body = skia.Path()
    by = 950 + breath
    body.moveTo(150, H + 40)
    body.cubicTo(170, by + 40, 330, by - 40, 540, by - 46)
    body.cubicTo(750, by - 40, 910, by + 40, 930, H + 40)
    body.close()
    c.drawPath(body, paint(rgb("#3F5D7A")))
    neck = skia.Path()
    neck.moveTo(478, 760)
    neck.lineTo(602, 760)
    neck.lineTo(612, by - 30)
    neck.lineTo(468, by - 30)
    neck.close()
    c.drawPath(neck, paint(rgb("#E3AE8E")))
    v = skia.Path()
    v.moveTo(462, by - 46)
    v.lineTo(540, by + 70)
    v.lineTo(618, by - 46)
    v.close()
    c.drawPath(v, paint(rgb("#E3AE8E")))

    c.save()
    c.rotate(sway, 540, 840)
    c.translate(0, breath * .6)
    hx, hy = 540, 600
    c.drawOval(skia.Rect.MakeXYWH(hx - 186, hy + 10, 40, 80), paint(rgb("#E3AE8E")))      # ears
    c.drawOval(skia.Rect.MakeXYWH(hx + 146, hy + 10, 40, 80), paint(rgb("#E3AE8E")))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(hx - 160, hy - 200, 320, 410), 150, 170), paint(rgb("#EDBB9C")))
    hair = skia.Path()
    hair.moveTo(hx - 172, hy + 30)
    hair.cubicTo(hx - 200, hy - 210, hx - 60, hy - 270, hx + 40, hy - 250)
    hair.cubicTo(hx + 170, hy - 240, hx + 210, hy - 120, hx + 172, hy + 30)
    hair.cubicTo(hx + 150, hy - 90, hx + 60, hy - 140, hx - 40, hy - 120)
    hair.cubicTo(hx - 110, hy - 110, hx - 150, hy - 60, hx - 172, hy + 30)
    hair.close()
    c.drawPath(hair, paint(rgb("#2E2522")))
    # eyes blink every few seconds
    ph = (t + .4) % 3.7
    open_ = 1 - max(0.0, 1 - abs(ph - .1) / .08) if ph < .2 else 1
    look = math.sin(t * .7) * 5
    for ex in (hx - 70, hx + 70):
        c.drawOval(skia.Rect.MakeXYWH(ex - 17 + look, hy + 8 - 21 * open_, 34, max(3, 42 * open_)), paint(rgb("#2A211E")))
        c.drawCircle(ex - 6 + look, hy - 4, 5 * open_, paint(rgb("#FFFFFF"), .9))
        brow = skia.Paint(AntiAlias=True, Color=skia.Color(*rgb("#2E2522")), StrokeWidth=12, Style=skia.Paint.kStroke_Style,
                          StrokeCap=skia.Paint.kRound_Cap)
        lift = 6 * talking(caps, t)
        c.drawLine(ex - 34, hy - 52 - lift, ex + 34, hy - 58 - lift, brow)
    c.drawCircle(hx - 112, hy + 92, 30, paint(rgb("#F08F84"), .35, 12))               # cheeks
    c.drawCircle(hx + 112, hy + 92, 30, paint(rgb("#F08F84"), .35, 12))
    nose = skia.Paint(AntiAlias=True, Color=skia.Color(*rgb("#C98D70")), StrokeWidth=9, Style=skia.Paint.kStroke_Style,
                      StrokeCap=skia.Paint.kRound_Cap)
    c.drawLine(hx, hy + 40, hx - 10, hy + 92, nose)
    m = talking(caps, t)
    if m > 0:
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(hx - 46, hy + 128, 92, 16 + 46 * m), 30, 30), paint(rgb("#7A2E2E")))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(hx - 30, hy + 128, 60, 12), 6, 6), paint(rgb("#FFFFFF"), .9))
    else:
        smile = skia.Path()
        smile.moveTo(hx - 50, hy + 136)
        smile.quadTo(hx, hy + 176, hx + 50, hy + 136)
        c.drawPath(smile, skia.Paint(AntiAlias=True, Color=skia.Color(*rgb("#7A2E2E")), StrokeWidth=11,
                                     Style=skia.Paint.kStroke_Style, StrokeCap=skia.Paint.kRound_Cap))
    c.restore()


def main():
    caps = captions()
    dur = round(caps[-1]["t1"] + 1.2, 3)
    shared = DEMO / "_build"
    shared.mkdir(exist_ok=True)
    clip = shared / "source.mp4"
    if not clip.exists():
        print(f"drawing the stand-in presenter ({dur:.1f} s) ...", flush=True)
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                                "-map", "0:v", "-map", "1:a", "-shortest", "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                                "-pix_fmt", "yuv420p", "-c:a", "aac", str(clip)], stdin=subprocess.PIPE)
        surf = skia.Surface(W, H)
        for f in range(int(dur * FPS)):
            c = surf.getCanvas()
            c.clear(skia.ColorWHITE)
            presenter(c, f / FPS, caps)
            enc.stdin.write(np.ascontiguousarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).tobytes())
        enc.stdin.close()
        if enc.wait():
            sys.exit("ffmpeg failed")
    src = dict(file="input/source.mp4", width=W, height=H, fps=float(FPS), duration=dur, aspect=f"{W}:{H}",
               crop=[294, 330, 492, 656], crop_note="demo stand-in")
    for name in ("whiteboard", "popcard", "softglass"):
        proj = DEMO / name
        (proj / "data").mkdir(parents=True, exist_ok=True)
        (proj / "input").mkdir(exist_ok=True)
        (proj / "data/source.json").write_text(json.dumps(src, indent=1), "utf-8")
        (proj / "data/captions.json").write_text(json.dumps(caps, ensure_ascii=False, indent=1), "utf-8")
        dst = proj / "input/source.mp4"
        if not dst.exists():
            shutil.copy2(clip, dst)
    print("demo projects ready:", ", ".join(f"demo/{n}" for n in ("whiteboard", "popcard", "softglass")))
    for ln in caps:
        print(f"{ln['t0']:6.2f}-{ln['t1']:6.2f}  {ln['zh']}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Chinese text on a Windows console or pipe
    main()
