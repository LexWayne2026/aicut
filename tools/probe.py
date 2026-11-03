"""Probe the talking-head footage: size, fps, duration, rotation, a face-aware portrait crop for the
corner photo, and adaptive silence detection (natural cut points).

    python tools/probe.py projects/my-video            # reads <project>/input/source.*, writes data/source.json

Face crop rule (from production feedback): 3:4 portrait, face centred horizontally, eyes ~1/3 from the
top, collar in frame, no shelf/ceiling band across the top. Uses OpenCV's Haar face detector on ~16
sampled frames (median box); falls back to a centred heuristic if OpenCV or a face is unavailable.
"""
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path


def ffprobe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate:stream_side_data=rotation:stream_tags=rotate:"
                          "format=duration", "-of", "json", str(path)], capture_output=True, text=True, check=True)
    d = json.loads(out.stdout)
    st = d["streams"][0]
    w, h = int(st["width"]), int(st["height"])
    rot = 0
    for sd in st.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(float(sd["rotation"]))
    rot = int(st.get("tags", {}).get("rotate", rot) or rot)
    if abs(rot) % 180 == 90:
        w, h = h, w
    num, den = st["r_frame_rate"].split("/")
    fps = float(num) / float(den or 1)
    return w, h, fps, float(d["format"]["duration"])


def sample_frames(path, w, h, duration, n=16, width=480):
    sh = int(round(h * width / w / 2) * 2)
    frames = []
    for i in range(n):
        t = duration * (i + 0.5) / n
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(path), "-frames:v", "1",
                              "-vf", f"scale={width}:{sh}", "-pix_fmt", "gray", "-f", "rawvideo", "-"],
                             capture_output=True).stdout
        if len(raw) == width * sh:
            frames.append(raw)
    return frames, width, sh


def face_crop(path, w, h, duration):
    try:
        import cv2
        import numpy as np
    except Exception:
        return None, "opencv-missing"
    frames, fw, fh = sample_frames(path, w, h, duration)
    if not hasattr(cv2, "CascadeClassifier"):          # OpenCV 5 removed Haar cascades
        return None, "opencv>=5-no-haar (pip install 'opencv-python-headless<5')"
    det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    if det.empty():                                    # OpenCV cannot open non-ASCII paths on Windows
        return None, "haar-cascade-not-loaded (keep the venv on an ASCII path, e.g. C:\\wbx-venv)"
    boxes = []
    for raw in frames:
        img = np.frombuffer(raw, np.uint8).reshape(fh, fw)
        faces = det.detectMultiScale(img, scaleFactor=1.1, minNeighbors=6, minSize=(fw // 14, fw // 14))
        if len(faces):
            x, y, bw, bh = max(faces, key=lambda f: f[2] * f[3])
            boxes.append((x, y, bw, bh))
    if len(boxes) < max(3, len(frames) // 4):
        return None, f"faces-found-{len(boxes)}"
    k = w / fw
    x = statistics.median(b[0] for b in boxes) * k
    y = statistics.median(b[1] for b in boxes) * k
    bw = statistics.median(b[2] for b in boxes) * k
    bh = statistics.median(b[3] for b in boxes) * k
    cx = x + bw / 2
    eye_y = y + bh * 0.42
    cw = min(w, bw * 1.8)
    ch = min(h, cw * 4 / 3)
    cw = ch * 3 / 4
    cy0 = eye_y - ch * 0.33
    cx0 = min(max(0, cx - cw / 2), w - cw)
    cy0 = min(max(0, cy0), h - ch)
    return [round(cx0), round(cy0), round(cw), round(ch)], f"faces-found-{len(boxes)}"


def fallback_crop(w, h):
    cw = min(w * 0.45, h * 0.75 * 0.75)
    ch = cw * 4 / 3
    return [round((w - cw) / 2), round(h * 0.16), round(cw), round(ch)]


def silences(path, min_d=0.4):
    """Adaptive silence detection: measure the EBU R128 gating threshold, use it as the noise floor."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-map", "0:a:0", "-af",
                        "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r'"input_thresh"\s*:\s*"(-?[\d.]+)"', r.stderr)
    thresh = float(m.group(1)) if m else -40.0
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-map", "0:a:0", "-af",
                        f"silencedetect=noise={thresh}dB:d={min_d}", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: (-?[\d.]+)", r.stderr)]
    return {"threshold_db": thresh, "silences": [[round(a, 3), round(b, 3)] for a, b in zip(starts, ends)]}


def main():
    proj = Path(sys.argv[1]).resolve()
    src = next((p for p in sorted((proj / "input").glob("source.*"))), None)
    if src is None:
        sys.exit(f"no input/source.* in {proj}")
    w, h, fps, dur = ffprobe(src)
    crop, why = face_crop(src, w, h, dur)
    if crop is None:
        crop = fallback_crop(w, h)
        print(f"!! face crop fallback ({why}) — check the corner photo and edit data/source.json 'crop' if needed")
    data = proj / "data"
    data.mkdir(exist_ok=True)
    meta = dict(file=str(src.relative_to(proj)), width=w, height=h, fps=round(fps, 3), duration=round(dur, 3),
                aspect=f"{w}:{h}", crop=crop, crop_note=why)
    (data / "source.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), "utf-8")
    sil = silences(src)
    (data / "silences.json").write_text(json.dumps(sil, indent=1), "utf-8")
    print(json.dumps(meta, ensure_ascii=False))
    print(f"silences: {len(sil['silences'])} (threshold {sil['threshold_db']} dB)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Chinese text on a Windows console or pipe
    main()
