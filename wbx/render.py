"""Render an aicut project (timeline.TEMPLATE picks the look: 1 whiteboard, 2 Pop Card, 3 Soft Glass).

    python wbx/render.py --project projects/my-video                 # final: source resolution, 60 fps
    python wbx/render.py --project projects/my-video --preview       # half resolution, 30 fps, fast
    python wbx/render.py --project ... --start 52 --end 75           # any segment
    python wbx/render.py --project ... --stills 3.5,30,70            # PNG stills into <project>/out/stills
    python wbx/render.py --project ... --mb 6                        # motion blur: 6 sub-frames, 180° shutter

The OUTPUT SIZE AND ASPECT FOLLOW THE SOURCE FOOTAGE (data/source.json, written by tools/probe.py):
a 1080x1440 clip renders 1080x1440, a 2160x3840 clip renders 2160x3840, 1920x1080 renders 1920x1080.
Every frame is a pure function of t, so segments render independently and concat losslessly.
"""
import argparse
import importlib
import json
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import skia

KIT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT))

from wbx import cues  # noqa: E402
from wbx import layout as LY  # noqa: E402
from wbx.core import (GRID, H as _AH, INK, PAPER, BLUE, MARKER, VIDEO, char_advances, clamp01, font, hexc,  # noqa: E402
                      lerp, on_video, paint, set_time, sketch, soft, spring)
from wbx.scene import draw_scenes  # noqa: E402

STATE = {"full": (0.0, 1.0), "pip": (1.0, 1.0), "hidden": (1.0, 0.0)}


class Project:
    def __init__(self, path):
        self.dir = Path(path).resolve()
        cues.load(self.dir)
        self.src = json.loads((self.dir / "data/source.json").read_text("utf-8"))
        sys.path.insert(0, str(self.dir))
        self.timeline = importlib.import_module("timeline")
        self.scenes = importlib.import_module("scenes")
        self.video = self.dir / self.src.get("file", "input/source.mp4")
        self.layout = LY.Layout(self.src["width"], self.src["height"])
        LY.set_current(self.layout)
        k = self.layout.k
        cx, cy, cw, ch = self.src["crop"]                          # face crop in source pixels
        self.crop = skia.Rect.MakeXYWH(cx * k, cy * k, cw * k, ch * k)
        self.duration = float(self.src["duration"])
        self.presenter = getattr(self.timeline, "PRESENTER", [(0.0, "full")])
        self.caption_mute = getattr(self.timeline, "CAPTION_MUTE", [])
        self.SCENES = self.scenes.SCENES
        self.captions_on = getattr(self.timeline, "CAPTIONS_ON", True)
        self.template = int(getattr(self.timeline, "TEMPLATE", 1))      # 1 whiteboard, 2 Pop Card, 3 Soft Glass


# ------------------------------------------------------------------ presenter
def presenter_state(P, t):
    """(m, v): m = 0 full-frame .. 1 corner photo, v = visibility. Spring-animated between keyframes."""
    pres = P.presenter
    m, v = STATE[pres[0][1]]
    for i in range(1, len(pres)):
        tk, st = pres[i]
        if t < tk:
            break
        tm, tv = STATE[st]
        km = spring(t - tk, w=8.5, z=0.86)
        kv = soft(t - tk, w=10) if tv < v else spring(t - tk, w=11, z=0.8)
        nxt = pres[i + 1][0] if i + 1 < len(pres) else 1e9
        if t < nxt:
            return lerp(m, tm, km), lerp(v, tv, kv), t - tk
        m, v = tm, tv
    return m, v, 99.0


def lerp_rect(a, b, p):
    return skia.Rect.MakeLTRB(lerp(a.left(), b.left(), p), lerp(a.top(), b.top(), p),
                              lerp(a.right(), b.right(), p), lerp(a.bottom(), b.bottom(), p))


def draw_presenter(c, P, img, t, scale):
    m, v, since = presenter_state(P, t)
    if v <= 0.003 or img is None:
        return m, v
    lay = P.layout
    FULL = skia.Rect.MakeWH(lay.W, lay.H)
    PIP, CROP = lay.pip, P.crop
    dst = lerp_rect(FULL, PIP, m)
    # one virtual camera: geometric zoom + gliding crop centre (face keeps its proportions)
    k = math.exp(lerp(0.0, math.log(PIP.width() / CROP.width()), m))
    sx, sy = lerp(CROP.centerX(), PIP.centerX(), m), lerp(CROP.centerY(), PIP.centerY(), m)
    src = skia.Rect.MakeLTRB((dst.left() - sx) / k + CROP.centerX(), (dst.top() - sy) / k + CROP.centerY(),
                             (dst.right() - sx) / k + CROP.centerX(), (dst.bottom() - sy) / k + CROP.centerY())
    sv = 0.82 + 0.18 * v
    cx, cy = dst.centerX(), dst.centerY()
    dst = skia.Rect.MakeXYWH(cx - dst.width() * sv / 2, cy - dst.height() * sv / 2, dst.width() * sv, dst.height() * sv)
    r = 10 * clamp01(m * 3) * sv
    src_px = skia.Rect.MakeLTRB(src.left() * scale, src.top() * scale, src.right() * scale, src.bottom() * scale)
    pin = clamp01(m * 2) * v
    # landing wobble: the photo swings a little when it lands in the corner
    wob = 3.0 * math.exp(-since * 4) * math.sin(since * 14) * pin if m > 0.5 else 0.0
    c.save()
    c.translate(cx, cy)
    c.rotate(-2.2 * m + wob)
    c.translate(-cx, -cy)
    if pin > 0.01:
        fm = 10 * pin
        fr = skia.Rect.MakeLTRB(dst.left() - fm, dst.top() - fm, dst.right() + fm, dst.bottom() + fm * 1.6)
        c.drawRRect(skia.RRect.MakeRectXY(fr.makeOffset(4, 12), r + 4, r + 4), paint("#4A5568", 0.22 * pin, blur=16))
        c.drawRRect(skia.RRect.MakeRectXY(fr, r + 4, r + 4), paint("#FFFFFF", pin))
        fp = skia.Path()
        fp.addRRect(skia.RRect.MakeRectXY(fr, r + 4, r + 4))
        sketch(c, fp, INK, 0.45 * pin, 1.8, 77)
    c.save()
    c.clipRRect(skia.RRect.MakeRectXY(dst, r, r), doAntiAlias=True)
    p = skia.Paint(AntiAlias=True)
    p.setAlphaf(v)
    c.drawImageRect(img, src_px, dst, skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear), p,
                    skia.Canvas.kFast_SrcRectConstraint)
    c.restore()
    if pin > 0.01:
        c.save()
        c.translate(dst.centerX(), dst.top() - 6)
        c.rotate(4)
        tape = paint("#EAD9A6", 0.78 * pin)
        tp = skia.Path()
        tp.addRect(skia.Rect.MakeXYWH(-55, -17, 110, 34))
        tape.setPathEffect(skia.DiscretePathEffect.Make(6, 1.6, 9))
        c.drawPath(tp, tape)
        c.restore()
    c.restore()
    return m, v


# ------------------------------------------------------------------ board
_BOARD = {}


def board(lay, scale):
    key = (lay.W, lay.H, round(scale, 4))
    if key not in _BOARD:
        w, h = int(round(lay.W * scale)), int(round(lay.H * scale))
        rng = np.random.default_rng(3)
        grain = (rng.standard_normal((h, w)) * 3.2).astype(np.float32)
        base = np.array([int(PAPER[i:i + 2], 16) for i in (1, 3, 5)], np.float32)
        arr = np.clip(base[None, None, :] + grain[..., None], 0, 255).astype(np.uint8)
        rgba = np.ascontiguousarray(np.dstack([arr, np.full((h, w, 1), 255, np.uint8)]))
        surf = skia.Surface(w, h)
        bc = surf.getCanvas()
        bc.drawImage(skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType), 0, 0)
        bc.scale(scale, scale)
        for i, x in enumerate(range(0, lay.W + 1, 40)):
            bc.drawLine(x, 0, x, lay.H, paint(GRID, 0.34 if i % 5 == 0 else 0.15, stroke=1.6 if i % 5 == 0 else 1.0))
        for i, y in enumerate(range(0, lay.H + 1, 40)):
            bc.drawLine(0, y, lay.W, y, paint(GRID, 0.34 if i % 5 == 0 else 0.15, stroke=1.6 if i % 5 == 0 else 1.0))
        g = skia.Paint()
        g.setShader(skia.GradientShader.MakeRadial(skia.Point(lay.W / 2, lay.H * 0.45), max(lay.W, lay.H) * 0.85,
                                                   [hexc("#FFFFFF", 0.0), hexc("#7A7360", 0.10)], [0.55, 1]))
        bc.drawRect(skia.Rect.MakeWH(lay.W, lay.H), g)
        _BOARD[key] = surf.makeImageSnapshot()
    return _BOARD[key]


# ------------------------------------------------------------------ captions (TikTok-style active character)
def caption_at(t):
    C = cues.CAPTIONS
    for i, ln in enumerate(C):
        nxt = C[i + 1]["t0"] if i + 1 < len(C) else ln["t1"] + 1.0
        if ln["t0"] - 0.05 <= t < min(nxt, ln["t1"] + 0.6):
            return ln
    return None


def draw_captions(c, P, t, opacity=1.0):
    mute = 0.0
    for a, b in P.caption_mute:
        if a - 0.2 < t < b + 0.2:
            mute = max(mute, clamp01(1 - abs(min(max(t, a), b) - t) / 0.2))
    if mute >= 0.999:
        return
    ln = caption_at(t)
    if ln is None:
        return
    lay = P.layout
    units = ln["highlight"]["units"]
    text = "".join(u["text"] for u in units).rstrip("，。、？！：；,.!?;:")
    size = 40
    adv = char_advances(text, size, 600)
    wid = sum(adv)
    maxw = lay.W - 2 * 72
    if wid > maxw:
        size = size * maxw / wid
        adv = char_advances(text, size, 600)
        wid = sum(adv)
    k = spring(t - ln["t0"] + 0.05, w=14, z=0.9)
    oe = 1 - clamp01((t - ln["t1"] - 0.35) / 0.25)
    alpha = clamp01(k * 1.4) * oe * (1 - mute) * opacity
    if alpha <= 0.003:
        return
    x = (lay.W - wid) / 2
    y = lay.caption_y + (1 - k) * 12
    lit, act = [], []
    pos = 0
    for u in units:
        for ch in u["text"]:
            if pos < len(text):
                lit.append(clamp01((t - u["start"]) / max(0.05, u["end"] - u["start"])))
                act.append(spring(t - u["start"], 16, 0.5) * (1 - clamp01((t - u["end"] - 0.05) / 0.2)))
            pos += 1
    f = font("hand", 600, size)
    onv = VIDEO["on"]
    for i, ch in enumerate(text):
        a = lit[i] if i < len(lit) else 1.0
        pop = act[i] if i < len(act) else 0.0
        col = (INK if a > 0.99 else ("#BDBDC6" if onv else "#6E6E76"))
        if pop > 0.05:
            col = MARKER if onv else BLUE
        c.save()
        cx = x + adv[i] / 2
        s = 1 + 0.14 * pop
        c.translate(cx, y - size * 0.35)
        c.scale(s, s)
        c.translate(-cx, -(y - size * 0.35))
        if onv:
            c.drawString(ch, x + 1, y + 2, f, paint("#000000", 0.6 * alpha, blur=4))
        c.drawString(ch, x, y, f, paint(col, (0.85 + 0.15 * a) * alpha))
        c.restore()
        x += adv[i]


# ------------------------------------------------------------------ frame
def render_frame(c, P, t, img, scale):
    if P.template == 2:
        from wbx import popcard
        return popcard.render_frame(c, P, t, img, scale)
    if P.template == 3:
        from wbx import softglass
        return softglass.render_frame(c, P, t, img, scale)
    set_time(t)
    lay = P.layout
    c.save()
    c.scale(scale, scale)
    LY.set_base_matrix(c.getTotalMatrix())
    c.save()
    c.resetMatrix()
    c.drawImage(board(lay, scale), 0, 0)
    c.restore()
    m, v, _ = presenter_state(P, t)
    if m > 0.01 or v < 0.99:
        draw_scenes(c, t, P.SCENES, "stage")
    draw_presenter(c, P, img, t, scale)
    full = (1 - m) * v
    if full > 0.01:
        g = skia.Paint()
        y0 = lay.H - 740
        g.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, lay.H)],
                                                   [hexc("#000000", 0.0), hexc("#0B0F1A", 0.42 * full),
                                                    hexc("#0B0F1A", 0.78 * full)], [0, 0.45, 1]))
        c.drawRect(skia.Rect.MakeWH(lay.W, lay.H), g)
        with on_video():
            draw_scenes(c, t, P.SCENES, "over")
    if P.captions_on:
        if full < 0.999:
            draw_captions(c, P, t, 1 - full)
        if full > 0.001:
            with on_video():
                draw_captions(c, P, t, full)
    fe = clamp01((t - (P.duration - 0.6)) / 0.5)
    if fe > 0:
        c.drawRect(skia.Rect.MakeWH(lay.W, lay.H), paint(PAPER, fe))
    c.restore()


# ------------------------------------------------------------------ io
def ff():
    return shutil.which("ffmpeg") or "ffmpeg"


def open_decoder(P, start, fps, w, h):
    if not P.video.exists():
        print(f"!! source video not found at {P.video} — rendering without presenter")
        return None
    cmd = [ff(), "-v", "error", "-ss", f"{start:.4f}", "-i", str(P.video), "-an",
           "-vf", f"fps={fps},scale={w}:{h}:flags=lanczos", "-pix_fmt", "rgba", "-f", "rawvideo", "-"]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=w * h * 4 * 4)


def open_encoder(out, fps, w, h, preview, encoder):
    cmd = [ff(), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-"]
    if encoder == "prores":
        cmd += ["-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le"]
    elif preview:
        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p"]
    else:
        cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p", "-x264-params",
                "aq-mode=3", "-tune", "film"]
    cmd += ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", str(out)]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--preview", action="store_true", help="half resolution, 30 fps, fast encode")
    ap.add_argument("--res-scale", type=float, default=None, help="output size relative to the source (1 = same)")
    ap.add_argument("--fps", type=int, default=None)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--encoder", choices=["x264", "prores"], default="x264")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--silent-out", default=None)
    ap.add_argument("--mb", type=int, default=1, help="motion-blur sub-frames (1 = off; 4-8 for the final)")
    ap.add_argument("--shutter", type=float, default=180.0, help="shutter angle for motion blur")
    ap.add_argument("--stills", default=None)
    a = ap.parse_args()

    P = Project(a.project)
    lay = P.layout
    rs = a.res_scale or (0.5 if a.preview else 1.0)
    w = int(round(P.src["width"] * rs / 2) * 2)
    h = int(round(P.src["height"] * rs / 2) * 2)
    scale = w / lay.W                                    # design units -> output pixels
    fps = a.fps or (30 if a.preview else 60)
    end = min(a.end or P.duration, P.duration)
    outdir = P.dir / "out"
    outdir.mkdir(exist_ok=True)
    arr = np.zeros((h, w, 4), np.uint8)
    surf = skia.Surface(arr)
    c = surf.getCanvas()

    def frame_img(raw):
        return skia.Image.fromarray(np.frombuffer(raw, np.uint8).reshape(h, w, 4).copy(),
                                    colorType=skia.kRGBA_8888_ColorType)

    if a.stills:
        sd = outdir / "stills"
        sd.mkdir(exist_ok=True)
        for ts in a.stills.split(","):
            t = float(ts)
            img = None
            if P.video.exists():
                raw = subprocess.run([ff(), "-v", "error", "-ss", f"{t:.4f}", "-i", str(P.video), "-frames:v", "1",
                                      "-vf", f"scale={w}:{h}", "-pix_fmt", "rgba", "-f", "rawvideo", "-"],
                                     capture_output=True).stdout
                if len(raw) == w * h * 4:
                    img = frame_img(raw)
            c.clear(skia.ColorBLACK)
            render_frame(c, P, t, img, scale)
            surf.makeImageSnapshot().save(str(sd / f"t{t:07.2f}.png"), skia.kPNG)
        print(f"stills -> {sd}")
        return

    tag = "preview" if a.preview else "master"
    ext = ".mov" if a.encoder == "prores" else ".mp4"
    silent = Path(a.silent_out) if a.silent_out else outdir / f"_video_{tag}_{a.start:.0f}-{end:.0f}{ext}"
    out = Path(a.out) if a.out else outdir / f"{P.dir.name}-{w}x{h}-{tag}.mp4"
    n = int(math.floor((end - a.start) * fps + 1e-6))
    dec = open_decoder(P, a.start, fps, w, h)
    enc = open_encoder(silent, fps, w, h, a.preview, a.encoder)
    fb = w * h * 4
    t_start = time.time()
    img = None
    acc = np.zeros((h, w, 4), np.float32) if a.mb > 1 else None
    print(f"rendering {P.dir.name}: {w}x{h} @ {fps} fps, {n} frames ({a.start:.1f}-{end:.1f}s)"
          + (f", motion blur x{a.mb}" if a.mb > 1 else ""), flush=True)
    for i in range(n):
        t = a.start + i / fps
        if dec is not None:
            raw = dec.stdout.read(fb)
            if len(raw) == fb:
                img = frame_img(raw)
        if a.mb > 1:
            acc[:] = 0
            span = (a.shutter / 360.0) / fps
            for j in range(a.mb):
                c.clear(skia.ColorBLACK)
                render_frame(c, P, t + span * (j / a.mb - 0.5), img, scale)
                acc += arr
            enc.stdin.write((acc / a.mb + 0.5).astype(np.uint8).tobytes())
        else:
            c.clear(skia.ColorBLACK)
            render_frame(c, P, t, img, scale)
            enc.stdin.write(arr.tobytes())
        if i % (fps * 5) == 0:
            el = time.time() - t_start
            print(f"  t={t:7.2f}s  frame {i}/{n}  {i / max(el, 1e-6):5.1f} fps  eta "
                  f"{el / max(1, i) * (n - i) / 60:5.1f} min", flush=True)
    enc.stdin.close()
    enc.wait()
    if dec is not None:
        dec.kill()
    print(f"video done in {(time.time() - t_start) / 60:.1f} min -> {silent}")
    if a.no_audio:
        return
    from wbx.audio import build_mix
    mix = build_mix(P, a.start, end)
    subprocess.run([ff(), "-v", "error", "-y", "-i", str(silent), "-i", str(mix), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "128k" if a.preview else "320k", "-shortest",
                    "-movflags", "+faststart", str(out)], check=True)
    print(f"done -> {out}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Chinese text on a Windows console or pipe
    main()
