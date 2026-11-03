# Template 3 style guide and API: Soft Glass

Code: `wbx/softglass.py`. Example: `examples/softglass/`. Set `TEMPLATE = 3` in `timeline.py`.

## Look
- **Ground:** flat lavender (`BG_T #E7E6FB` to `BG_B #DCDEF8`) with faint white 45° lines and two very soft glows, lilac top-right and sky bottom-left. The renderer draws it full-bleed behind every stage scene; scenes never paint their own background.
- **Few rectangles.** Type, numbers and glass sit straight on the ground. At most one main white `card` per scene (a chart, an option grid's tiles). No container panels, no cards inside cards.
- **Frosted glass** (`glass`, `glass_pill`) really blurs what is behind it. Use it over video (labels, rows, badges) and for small round badges on the ground.
- **Colour:** navy `#1B1D3F` text, mute `#8D90B2` secondary, the house gradient lilac `#A28BF3` to sky `#5DBDE3` (`grad`) for big numbers, the highlighted bar and the main button. `ACCENT #7A7CF0` is the only solid accent. `SOFTS` holds pastel pairs for `orb`s and side cards.
- **Flat:** shadows are whispers (alpha under .1); no rims, no gloss, no outlines except the gradient selection `outline`.
- **Icons:** `glyph` monoline icons (tablet capsule coated lipo gummy drop bottle swap hex up), white inside an `orb` or ink with `line=True`.
- **Type:** Outfit SemiBold/Medium for Latin and numerals, Noto Sans SC Bold/Medium for Chinese (`wt="b"`/`"m"`). Headline 84-100 centred, secondary 32-44, 66 side margin. Big numbers use `roll` with `grad` as the paint.
- Text on screen is the speaker's own words or a literal condensation. No invented numbers.

## Presenter
- **Always live video.** Each slot carries a corner radius and a crop: `(x, y, w, h, radius, crop)`, crop 0 = whole frame, 1 = face, above 1 tighter. Named slots: `hero` (big centre card), `center`, `avatar` / `avatar_r` (round, top-left / top-right), `tl tr bl br left right`. Moves spring without arcs.
- A good rhythm: full frame for the hook, `hero` while the headline builds, then shrink to `avatar` when a chart or grid needs the room.
- **Full frame:** no white panels over the video. Glass rows and white text on the bottom gradient only.

## Motion
| Verb | Call | Use for |
|---|---|---|
| Rise | `rise(c, t, t0, cx, cy, draw, dy, w, z, s0, blur)` | The house entrance: slide up, scale in, come into focus |
| Pop | `pop(c, t, t0, cx, cy, draw)` | Small things: dots, icons, values |
| Odometer | `roll(c, frm, to, x, y, size, paint, t, t0)` | Every number that changes |
| Exit | `fade_out(c, t, t1, cx, cy, draw)` | Shrink, drift up, blur away |
| Slide | `q = slide(t, t0)` | Moving a ring or a group between two states |
| Pulse / ripple | `pulse(t, t0)`, `ripple(c, x, y, t, t0)` | Emphasis on a word |
| Frost cut | automatic | Frame frosts to lavender before every stage scene starts or ends, then focus-pulls in. `enter=None` on a scene opts out |

`draw` is a zero-argument lambda in absolute reference coordinates; `cx, cy` is the pivot.

## Scenes
`SCENES = [dict(t0, t1, fn, layer="stage"|"over", enter="frost"|None)]`. `fn(c, t)` draws in the 1080x1440 reference space (auto-fitted to any aspect). Stage scenes sit under the presenter; `over` scenes above it (glass on the video, hook text). With no scene active, a full-frame presenter with captions shows.
Helpers: `text text_w digit_w roll card glass glass_pill button orb bar outline chevrons glyph grad lin`.

## Sound
Sound effects on every visual event, no music by default (`MUSIC = None`). Master -14 LUFS, true peak at most -1 dB. `pop`, `tick`, `chime`, `rise` and `swish` suit this look.

## Feedback log (keep appending)
- First attempt (Soft UI: grey ground, nested white cards, black buttons, cursor) had too many rectangular backgrounds.
- Wanted instead: clean background with subtle diagonal lines, flat, simple and bright yet sophisticated, frosted-glass blur. This template is that version, approved from the motion test.
