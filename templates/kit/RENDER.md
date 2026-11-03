# Render kit

Self-contained: engine (`wbx/`), fonts (the project's template only, OFL; licences in `fonts/`), music (Holizna, CC0) and the project in
`projects/<name>/` (scenes, cues, transcript, source clip). The output matches the source clip's
resolution and aspect ratio automatically.

## Setup (macOS / Windows / Linux)

Needs Python 3.10+ and ffmpeg on PATH (`ffmpeg -version`).

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Render

```bash
# all CPU cores, source resolution, 60 fps  ->  projects/<name>/out/<name>-master.mp4
python wbx/parallel.py --project projects/<name>

# add motion blur (6 sub-frames, 180° shutter; ~6x slower, smoother fast moves)
python wbx/parallel.py --project projects/<name> --mb 6

# single process / quick checks
python wbx/render.py --project projects/<name> --preview
python wbx/render.py --project projects/<name> --start 50 --end 70
python wbx/render.py --project projects/<name> --stills 12,40,90
python wbx/render.py --project projects/<name> --encoder prores      # ProRes 422 HQ for grading
```

Frames are deterministic (frame = f(t)): segments can be rendered on several machines and joined with
`ffmpeg -f concat -c copy`. Expect roughly 0.1–0.3 s per full-res frame per core.
