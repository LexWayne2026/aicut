# Storyboarding a talking-head explainer

## From transcript to beats
1. Read `data/transcript.txt` end to end. Mark the structure: hook (first 5–8 s), thesis, chapters
   (often announced: "第一步… 第三步…", "first… second…"), examples with numbers, verdict lines, ending.
2. One idea per scene. A scene usually spans 1–4 caption lines (5–15 s). Split long explanations into
   sub-scenes (e.g. "drug" then "supplement") instead of crowding one board.
3. Every visual beat lands on a word: define cues in `timeline.T` with `at(line, word)`. Elements enter
   on (or ~0.1 s before) the word that names them. Never hard-code seconds.
4. Use `pauses()` / `data/silences.json` for scene cuts and transitions — cut in the breath, not mid-word.

## Presenter choreography
- `full` for: the hook/title, thesis statements, "remember…" verdicts, the closing line. Pair with a
  lower-third (layer "over") that says the line in big handwritten type + doodles; mute captions there.
- `pip` (taped corner photo) for explanations; `hidden` when the board needs the whole frame.
- Switch on phrase boundaries (≥ 1.5 s apart). Each morph gets a "swish" sfx.

## Motion vocabulary (pick per beat, vary across the video)
| beat | treatment |
|---|---|
| introduce a thing | `icon_in` draws it, label rises in; product objects (`bottle`, `tablet`) pop with spring |
| compare A vs B | two paper cards / bars; A appears, then B; highlight the difference (marker, bracket, gap line) |
| a number | `counter` rolls, `bar_chart` grows, `progress_ring` fills; show units |
| a rule / definition | `stamp` slam ("药品", "OK", "NO") or `sticky` note |
| "not equal" / myth | `neq` drawn + red `annotate(... "strike"/"crossed")` + knock sfx |
| list / steps | `checklist`, numbered doodle circles, chapter header with progress bar + icon |
| process / decision | flow nodes connected by drawn lines, icons at the right end |
| overlap / duplication | Venn with hatched intersection |
| emphasis | highlighter swipe, circle, squiggle underline, sparkle, burst lines |
| finale | bouncing big type, highlighter + squiggle, confetti, bell |

## Remotion-derived principles (adopted from remotion-dev/skills)
- Drive everything from time with explicit keyframes (`interpolate`) and clamp; ease entrances with
  `bezier(0.16, 1, 0.3, 1)`, moves with in-out, use heavily damped "push" springs when bounce is wrong.
- Animate scale perceptually (geometric), not linearly.
- Posterize deliberately for hand-made feel (line boil at 6 fps) — never posterize the camera or text.
- Treat scenes as a TransitionSeries: consecutive scenes with presentations (slide, wipe, iris, flip) and
  overlays at cut points (light-leak "flash") that don't shorten the timeline.
- Text annotations follow rough-notation: highlight, circle, underline, strike-through, crossed-off, box,
  bracket — always progress-driven so they draw on.
- Optional motion blur by sub-frame averaging (`--mb 6`, 180° shutter) for the final render.
- Captions: one line at a time, active word highlighted (TikTok style); keep inside the safe area.
- Video layout: decide what the viewer notices first in each scene; keep key text ≥ 80 px from the sides;
  headline ≥ 84 px, important supporting text ≥ 44 px (scale with width); no redundant elements.

## Checklist before preview
- Stills sheet covers every scene + a transition mid-way + every full-frame overlay.
- Smoke test: render every 0.1 s at tiny scale (catches exceptions in rarely-hit branches).
- Nothing overlaps the corner photo (x > ~780, y < ~380 in stage space near the top), header or captions.
- Every element that appears has a sound in `sfx_events()`.
