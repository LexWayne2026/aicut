---
name: aicut
description: Turn a talking-head (口播) clip into an animated explainer video in one of three templates. Template 1 is a grid whiteboard with pencil drawing, handwritten type, stamps, stickies, music and foley. Template 2 is Pop Card, with white cards, vibrant colour, inked cartoon objects, bouncy motion graphics, sound effects without music, and live presenter video in any position. Template 3 is Soft Glass, a flat lavender ground with faint diagonal lines, frosted glass, lilac-to-sky gradients, few cards and springy focus-pull motion. Output resolution and aspect ratio automatically match the source clip. Use when the user provides spoken-word footage and wants motion graphics, an explainer, 口播动画, "Template 1", "Template 2" or "Template 3", or calls aicut. Delivers a low-res preview plus a self-contained render kit (zip) for rendering on another machine.
---

# aicut: explainer video from a talking-head clip

You are the director. The user supplies a talking-head clip; you produce a preview video and a render kit.

## Choose the template first

The user picks when calling, e.g. "aicut Template 2". If they name none, ask which one before scaffolding.

| | Template 1: Whiteboard | Template 2: Pop Card | Template 3: Soft Glass |
|---|---|---|---|
| Look | Grid paper, pencil, handwritten type | White cards, vibrant colour, inked cartoon objects, rounded type | Flat lavender, faint diagonal lines, frosted glass, lilac-sky gradient, few cards |
| Motion | Draw-on, stamps, eraser wipes | Bouncy MG: pop, whip, drop, sheet slam | Rise into focus, odometer numbers, frost cuts |
| Presenter | Full frame, taped corner photo, hidden | Live video in any slot, moved by springs | Live video: hero card, round avatar or any slot |
| Sound | Music bed + foley | Sound effects, no music | Sound effects, no music |
| Style rules | `references/template-1-whiteboard.md` | `references/template-2-popcard.md` | `references/template-3-softglass.md` |
| API | `references/components.md` | `references/template-2-popcard.md` | `references/template-3-softglass.md` |
| Example | `examples/otc/` | `examples/popcard/` | `examples/softglass/` |
| Starter | `templates/project/` | `templates/project-popcard/` | `templates/project-softglass/` |

`examples/` exists only on the author's machines (it quotes a private clip). `demo/whiteboard`, `demo/popcard` and
`demo/softglass` are public, complete projects on one made-up script (`python demo/make_demo.py` builds their stand-in
clip and data); copy patterns from them when `examples/` is missing.

Read the chosen template's reference before designing anything; it holds the visual rules and the user's past
feedback. `references/storyboarding.md` covers pacing and animation principles for both. Never mix
templates' components in one project.

Engine: Python + skia (`wbx/`), deterministic frame = f(t), ffmpeg for I/O. KIT = this skill's folder.

## Environment (once per machine)

```bash
python3 -m venv ~/.wbx-venv && ~/.wbx-venv/bin/pip install -r KIT/requirements.txt \
    "opencv-python-headless>=4.8,<5" faster-whisper
```
Use `~/.wbx-venv/bin/python` for every command below. ffmpeg (with ffprobe) must be on PATH.

**Windows:** `KIT/install-windows.bat` copies the skill to `%USERPROFILE%\.claude\skills\aicut` and creates the venv
at `%USERPROFILE%\.wbx-venv`, or at `C:\wbx-venv` when the user name has non-ASCII characters (OpenCV cannot open
such paths). Python is then `~/.wbx-venv/Scripts/python.exe` or `C:/wbx-venv/Scripts/python.exe` (Claude Code runs
Git Bash); use whichever exists. ffmpeg: `winget install Gyan.FFmpeg`. Symlinks need Developer Mode, so `--link`
falls back to a hard link or a copy.

## Workflow

1. **Scaffold + probe + transcribe** (put projects next to the user's footage, e.g. `<workdir>/projects/<name>`):
   ```bash
   python KIT/tools/new_project.py <clip> <workdir>/projects/<name> --link --lang zh --model large-v3 --template <1|2|3>
   ```
   Writes `data/source.json` (size, fps, duration, face-aware 3:4 crop, silences) and `data/captions.json`
   (+ `transcript.txt`). On a slow machine use `--model small` and expect more ASR mistakes.
2. **Fix the transcript with the user.** Show `transcript.txt`; ask them to confirm terms. ASR errors
   (e.g. 算是补充剂 → 膳食补充剂) must be corrected in `captions.json` (both `zh` and the unit texts)
   before storyboarding — on-screen text must be what the speaker actually said.
3. **Storyboard** in `timeline.py` (cues via `at()`, presenter states, caption mutes, sfx events, music)
   and `scenes.py` (scene functions + `SCENES` registry). `timeline.TEMPLATE` selects the look. Follow `references/storyboarding.md`:
   one idea per scene, every beat on a word cue, presenter full-frame for hooks/verdicts/ending. Template 1 uses
   the corner photo for explanations, hidden for dense grids, and the asset library generously (icons draw on,
   stamps, stickies, counters, charts, annotations, transitions). Template 2 places the presenter wherever the
   layout leaves room, not just the top-right, and gives each element a motion verb. Template 3 keeps rectangles
   few: type and glass sit on the ground, one main card per scene at most. The user asked for rich motion.
   Text on screen must be literally true to the speech (no invented numbers or claims).
4. **Check stills** (cheap): `python KIT/wbx/render.py --project P --res-scale 0.5 --stills t1,t2,...`
   then `python KIT/tools/sheet.py P --cols 6` and look at the sheet. Check every scene, transitions
   mid-way, full-frame overlays, and the corner photo framing. Also smoke-test all times:
   render every 0.1 s at tiny scale (see examples) to catch exceptions before a long render.
5. **Preview**: `python KIT/wbx/render.py --project P --preview` (half resolution, 30 fps, with audio).
   Verify loudness (`ffmpeg -i out.mp4 -af ebur128=peak=true -f null -` → about -14 LUFS, peak ≤ -1 dB)
   and a contact sheet of the video (`tools/sheet.py P --video out/<file>.mp4`). Send the preview to the user.
6. **Render kit**: `python KIT/tools/package.py P` → `<name>-render-kit.zip` (engine, fonts, music, project,
   source clip). Do NOT render the final master locally unless asked; the user renders on a faster machine
   (`python wbx/parallel.py --project projects/<name>`, optional `--mb 6` motion blur).

Iterate on feedback by editing scenes/timeline and re-running steps 4–6. Keep feedback-derived rules in
the chosen template's reference up to date when the user states a new preference.

## Adaptive output

`wbx/layout.py` sets the design space from the source (short side = 1080 units). Template 1 fits the authored stage
(x 0..1080, y 320..1260) into the free area, with header, corner photo, lower thirds and captions anchored to the
real frame. Templates 2 and 3 fit their 1080x1440 reference space, with backgrounds bleeding to the edges and captions anchored
to the real frame. 3:4, 9:16, 4:5, 1:1 and 16:9 all work without scene changes. Output pixels = source pixels.
