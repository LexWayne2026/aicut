# Template 1 component API cheat-sheet (wbx)

Template 2 has its own API in `template-2-popcard.md`, Template 3 in `template-3-softglass.md`.

Every function draws at absolute time `t`; `t0` is the cue it reacts to. Colours: INK MUTE BLUE GREEN AMBER RED CYAN MARKER.

## core
| call | what |
|---|---|
| `draw_text(c, s, x, baseline, size, weight, color, align, t=t, t0=cue, stagger, style="rise"/"bounce", t1=exit_cue)` | handwritten text; chars spring in (rise+blur) or bounce (drop, tilt, overshoot); blur-out after `t1`; returns width |
| `draw_label(c, s, x, y, size, color, ...)` | tracked kicker label |
| `text_width(s, size, weight)` | measure |
| `glass(c, x, y, w, h, r, tint=, glow=)` | paper card with pencil outline + shadow |
| `pill(c, cx, cy, s, size, color, t=, t0=, align="left"/"center", t1=)` | springy tag |
| `marker(c, x, y, w, h, p)` | highlighter swipe (progress p) |
| `line_draw(c, pts, p, color, a, width, dash=)` | pencil polyline drawn on |
| `arrow`, `check`, `cross`, `neq`, `arc` | drawn-on symbols |
| `doodle_circle`, `squiggle`, `sparkle(c,x,y,s,t,t0)`, `burst(c,x,y,r0,r1,n,t,t0)` | hand-drawn emphasis |
| `bottle`, `tablet`, `form_icon(kind)` | product objects (kinds: plain sr coated lipo gummy liquid) |
| `layer(c, alpha, blur, scale, cx, cy, dx, dy)` | group transform/opacity/blur (context manager) |
| `spring(dt, w, z)`, `soft(dt, w)`, `EXPO_OUT(p)`, `SMOOTH(p)`, `bezier(...)`, `push(p)` | easing |
| `interpolate(t, [t0,t1,...], [v0,v1,...], easing=[...], posterize=fps)` | Remotion-style keyframes |
| `pscale(p, s0, s1)` | perceptual scale |
| `on_video()` | context: white/bright palette + text shadows (used automatically for "over" scenes) |

## icons (draw-on)
`icon_in(c, name, cx, cy, size, t, t0, dur=0.9, color=INK, accent=MARKER, alpha=1, idle=True)` — pops in while
being drawn stroke by stroke, accent hatch fills last, then idles (float + tilt).
`draw_icon(c, name, cx, cy, size, p, color, accent, alpha)` — manual progress.
Names: bottle pill tablet capsule coin coins price_tag cart wallet money_bag magnifier clipboard document shield
heart brain bulb flask leaf drop clock calendar chart_bar chart_pie chart_line person people thumbs_up warning star
target scale gift home apple bowl stomach question exclaim speech check_circle cross_circle trophy rocket gear lock
dna atom. Add new ones in `wbx/icons.py` (100x100 box: strokes in drawing order + accent fills).

## components
| call | what |
|---|---|
| `annotate(c, kind, x, y, w, h, p, color)` / `annotate_text(c, kind, text, x, baseline, size, p, color)` | underline · squiggle · highlight · box · circle · strike · crossed · bracket |
| `stamp(c, text, cx, cy, t, t0, color, size, rot, sub=)` | rubber stamp slam + ink splatter (sfx "stamp") |
| `sticky(c, text, cx, cy, t, t0, color, w, h, rot, size, lines=)` | sticky note swings on (sfx "flap") |
| `counter(c, x, y, size, t, t0, t1, v0, v1, fmt, color, align, weight)` | rolling number |
| `bar_chart(c, x, y, w, h, values, labels, t, t0, colors, unit=)` | bars grow + count up |
| `donut(c, cx, cy, r, fracs, colors, t, t0, labels=)` | hatched ring segments sweep in |
| `line_chart(c, x, y, w, h, values, t, t0, color)` | line draws through dots |
| `progress_ring(c, cx, cy, r, frac, t, t0, color, label)` | ring fills |
| `callout(c, anchor_xy, note_xy, text, t, t0, color)` | curved arrow + note |
| `checklist(c, x, y, items, times, t, size)` | boxes tick off on cues |
| `typewriter(c, text, x, y, size, t, t0, cps)` | typed text with caret |
| `confetti(c, cx, cy, t, t0, n, spread)` | pencil confetti burst |
| `ambient(c, t, (x0,y0,x1,y1), n, seed, a)` | drifting margin doodles |

## scenes (TransitionSeries-style)
`SCENES = [dict(t0, t1, fn, layer="stage"|"over", space="stage"|"frame"|"lower", enter=..., exit=..., enter_dur, exit_dur, camera=True, flash=False)]`
- presentations: `blur` (default exit) `slide-left/right/up/down` `wipe` (eraser) `iris` `flip` `page` `pop`
- `flash=True` → warm paper light-leak at the cut; `camera` → slow push-in + drift.
- `with frame(c):` inside a stage scene draws in frame coordinates (headers at X0=64, y 118/196).

## timeline.py contract
`T` (dict of cues from `at()`), `PRESENTER` [(time, "full"|"pip"|"hidden")], `CAPTION_MUTE` [(a, b)],
`sfx_events()` → [(kind, time)], `MUSIC` (clouds | blue-skies | new-shoes | puppy-love | None), `MUSIC_DB`,
`TARGET_LUFS`, optional `CAPTIONS_ON`.
SFX kinds: pop tick scribble marker paper swish deny rise chime stamp erase flap draw.
