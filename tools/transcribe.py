"""Transcribe the talking-head clip into data/captions.json with per-character (CJK) or per-word timings.

    python tools/transcribe.py projects/my-video                    # model large-v3, language auto
    python tools/transcribe.py projects/my-video --model small --lang zh

Uses faster-whisper (pip install faster-whisper). Lines break at punctuation, at long pauses, or past
~16 CJK characters / ~7 Latin words. ALWAYS show the transcript to the user and fix ASR mistakes
(e.g. a misheard term) in data/captions.json before storyboarding — the on-screen text must match
what the speaker actually said.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

import numpy as np

PUNCT = "，。！？、；：,.!?;:"
CJK = re.compile(r"[㐀-鿿豈-﫿]")
ZH_PROMPT = "以下是普通话的句子，使用简体中文，带标点符号。"


def to_simplified(s):
    try:
        from opencc import OpenCC  # optional
        return OpenCC("t2s").convert(s)
    except Exception:
        return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--lang", default=None, help="e.g. zh, en; auto-detect if omitted")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--compute", default="auto", help="int8 on CPU is fastest; float16 on CUDA")
    ap.add_argument("--max-cjk", type=int, default=16)
    ap.add_argument("--max-words", type=int, default=7)
    a = ap.parse_args()

    from faster_whisper import WhisperModel
    proj = Path(a.project).resolve()
    src = next(iter(sorted((proj / "input").glob("source.*"))))
    model = WhisperModel(a.model, device=a.device, compute_type=a.compute)
    # decode with ffmpeg ourselves (avoids PyAV version issues): 16 kHz mono float32
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-map", "0:a:0", "-ac", "1", "-ar", "16000",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    audio = np.frombuffer(pcm, np.float32).copy()
    segs, info = model.transcribe(audio, language=a.lang, word_timestamps=True, vad_filter=True,
                                  initial_prompt=ZH_PROMPT if (a.lang or "").startswith("zh") else None,
                                  beam_size=5)
    lang = info.language
    cjk = lang in ("zh", "ja", "ko") or (a.lang or "").startswith(("zh", "ja", "ko"))
    words = []
    for s in segs:
        for wd in s.words or []:
            txt = to_simplified(wd.word) if lang == "zh" else wd.word
            if cjk:
                txt = txt.strip().translate(str.maketrans({",": "，", "?": "？", "!": "！", ":": "：", ";": "；",
                                                           ".": "。"}))
            if txt:
                words.append((txt, float(wd.start), float(wd.end)))
    # explode CJK words into characters (punctuation sticks to the previous char)
    units = []
    for txt, st, en in words:
        if cjk:
            chars = [ch for ch in txt]
            body = [ch for ch in chars if ch not in PUNCT]
            n = max(1, len(body))
            k = 0
            for ch in chars:
                if ch in PUNCT and units:
                    units[-1]["text"] += ch
                    continue
                t0 = st + (en - st) * k / n
                t1 = st + (en - st) * (k + 1) / n
                units.append({"text": ch, "start": round(t0, 3), "end": round(t1, 3)})
                k += 1
        else:
            units.append({"text": txt if txt.startswith(" ") or not units else " " + txt.strip(),
                          "start": round(st, 3), "end": round(en, 3)})
    # group into lines
    lines, cur = [], []

    def flush():
        if cur:
            text = "".join(u["text"] for u in cur).strip()
            lines.append({"id": f"c{len(lines):03d}", "t0": cur[0]["start"], "t1": cur[-1]["end"], "zh": text,
                          "highlight": {"source": "faster-whisper", "language": lang, "units": list(cur)}})
            cur.clear()

    def natural_split():
        """Line is too long: split at the biggest pause among the last few units, keep the rest."""
        tail = range(max(1, len(cur) - 7), len(cur))
        j = max(tail, key=lambda k: cur[k]["start"] - cur[k - 1]["end"])
        rest = cur[j:]
        del cur[j:]
        flush()
        cur.extend(rest)

    for u in units:
        if cur and u["start"] - cur[-1]["end"] > 0.6:
            flush()
        cur.append(u)
        n = sum(1 for x in cur for ch in x["text"] if CJK.match(ch)) if cjk else len(cur)
        limit = a.max_cjk if cjk else a.max_words
        if u["text"][-1:] in PUNCT:
            flush()
        elif n >= limit:
            natural_split()
    flush()
    # merge orphans (1-2 characters / a single word) into the previous line when they follow closely
    merged = []
    for ln in lines:
        short = len(ln["zh"].strip(PUNCT)) <= (2 if cjk else 1)
        if merged and short and ln["t0"] - merged[-1]["t1"] < 0.5:
            prev = merged[-1]
            prev["highlight"]["units"] += ln["highlight"]["units"]
            prev["zh"] = "".join(u["text"] for u in prev["highlight"]["units"]).strip()
            prev["t1"] = ln["t1"]
        else:
            merged.append(ln)
    for i, ln in enumerate(merged):
        ln["id"] = f"c{i:03d}"
    lines[:] = merged
    data = proj / "data"
    data.mkdir(exist_ok=True)
    (data / "captions.json").write_text(json.dumps(lines, ensure_ascii=False, indent=1), "utf-8")
    txt = "\n".join(f"{ln['t0']:7.2f}-{ln['t1']:7.2f}  {ln['zh']}" for ln in lines)
    (data / "transcript.txt").write_text(txt + "\n", "utf-8")
    print(txt)
    print(f"\n{len(lines)} lines, language={lang} -> {data / 'captions.json'}")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Chinese text on a Windows console or pipe
    main()
