# <Company> · <duration> s · <format> — structure

## Rules for this film
1. Nothing fades in; things change shape.
2. No cuts; every scene comes out of the last one.
3. Something happens on every beat.
4. Things bounce a tiny bit when they land (LAND / MORPH).
5. The camera does one move at a time.
6. Every click and whoosh has a real sound, placed by its measured peak.
7. It checks its own work (studio/check_film.py) before anyone watches it.
<edits agreed with the client, if any>

## Timing base
- Music: <track> (<source, licence>), <bpm> BPM. Starts at <music.start> s of the track so the drop lands at <t> s (<the moment>).
- Beat n = <60/bpm>·n s. Downbeats every 4th beat: b<k>, …
- <format, fps>

## Scene chain (no cuts)
| # | Time · beats | Copy | What happens | Camera (one move) | Out → next scene |
|---|---|---|---|---|---|
| 1 | 0.0–… · b0–b… | | | | **<shape that carries over>** |

## Beat map (every beat)
| Beats | Events |
|---|---|
| b0–b… (sc 1) | b0 … · **b3** … |

## Cue list
| Sound | Events (s) | Notes |
|---|---|---|
| whoosh | | fast moves only |
| click | | every cursor click |

## Product content used (verbatim)
| Scene | String / image | Source (screen, date, environment) |
|---|---|---|
