# Music and sound (phase 5)

## Choosing the track
- ~120 BPM makes a beat 0.5 s — comfortable for UI moves and typing. A clear **drop** gives the film its hinge (brand reveal / first product moment); a quieter **breakdown** is where the key message can linger; the **return** can carry the end card.
- Screen before downloading. Many libraries expose metadata or a waveform (Mixkit: JSON-LD on genre pages lists `url` and `waveformUrl`; the waveform JSON is peak pairs at ~0.2 s). Rank tracks by the largest loudness jump after the intro (compare 4 s before/after each point). Tempo from the waveform is only rough — measure after download.
- Present 1–3 candidates with filename, source URL, size (HEAD request `Content-Length`) and licence, then wait for approval.

## Measuring
`python studio/analyze_audio.py` (reads project.json) prints and saves:
- BPM, first beat and first downbeat, `grid_check` (kick energy on vs off the beat — if kicks sit off the grid, the grid locked onto hi-hats; the script fits on the kick band to avoid this, but look at `audio/analysis.png`),
- drop candidates (exact onset, dB jump, offset from grid),
- a **bar map** (start, dB, kick) — this is how you see intro / drop / breakdown / return, and where 4- or 8-bar phrases start,
- per SFX: sample peak, onset, tail, individual hits (keystrokes), and `level_build_db` (a riser must actually build).

## Placing the music
- `music.start` = drop time in the track − the film time where the drop should land (`--drop-at <s>` prints it). Starting on a downbeat keeps every film beat on a kick: the video's beat n falls at n·beat + (downbeat offset), usually within a few ms — under one frame.
- Need drop + breakdown + return in a short film? Edit the music: splice on downbeats at 4/8-bar phrase boundaries (e.g. first half of one phrase + second half of another) with 10 ms equal-power crossfades. Tell the user you can't listen and ask them to confirm the edit by ear.
- Fade the music out over the last ~1.2 s; the picture can hold (≤1 s) on the end card.

## Placing SFX
- One sound per event type: typing (keystrokes), whoosh (fast moves: floods, flights, pull-backs), click (every cursor click), pop (landings, chips, rows — quiet, pitch-varied), chime (a resolved moment), impact (the drop/brand hit).
- **Sounds mark what the eye notices** (settled in a client review, after two wrong tries):
  - a **reveal** (word sweep, text rising from a mask, a pill or card growing) sounds at its **onset** — the first letters/edges visible. Start reveals on beats (risers lead by ~0.06 s so they're visible on the beat) and their sounds sit on the grid;
  - a **landing** (a dot hopping or dropping onto its spot) sounds at the **impact** — use `landTime()` from the kit for spring landings;
  - **one sound per moment**: when two things happen together, one sound; keep sounds ≥150 ms apart.
  Putting a reveal's sound at its completion makes every sound late and piles them up at the end of a section; putting a landing's sound at its start makes it early. Verify with `studio/sync_probe.py` (per-region onset/arrival vs sound, plus a list of sounds closer than 150 ms).
- Place by **measured peak**, not by file start: a whoosh that peaks at 1.088 s must start 1.088 s before its event. `mix_audio.py` does this from the timeline; the composition only records events (`ev(t, 'whoosh', 'what')`).
- Balance is adaptive (sound vs music around each peak) with limits in `project.json → sfx_balance`. The self-check reports each kind's range; aim for whooshes/clicks a few dB over the music, pops and keys under it.
- Loudness: −14 LUFS integrated, −1 dBTP for social/web (YouTube, Instagram, LinkedIn normalise around there).
- Voice-over or product audio (e.g. an audio-summary feature): only the real audio for the real item shown. If it isn't available, show the player silent rather than using another item's audio.

## Downloading
- Ask first (filename, source, size). Save under `audio/` with descriptive names (`sfx_whoosh_<id>.wav`, `music_<title>_<id>.mp3`) and record source + licence in `brand/INTAKE.md` decisions log.
