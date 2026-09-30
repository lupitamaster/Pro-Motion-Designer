# Structure (phases 4 and 6)

## Breaking down a reference video
1. `python studio/reference_frames.py <video> out/ref --fps 2` → sheets of 16 frames with timestamps + `palette.txt`.
2. Read every sheet. Write `brand/REFERENCE_BREAKDOWN.md`:
   - **Big shape**: acts (problem → brand → mechanism → proof → payoff), where the palette flips (dark/light often marks chapters).
   - **Beat by beat table**: time, what happens, camera/motion, transition out.
   - **Transition vocabulary** worth stealing (e.g. typewriter that pushes the line; focus pull into a UI macro; pull-back reveal; object inside the sentence; scan + highlight boxes; a motif that flips the palette; isolate one row; morph chain button → pill → ring → check; card shrinks to reveal the next world).
   - **Camera**: 2.5D tilts, orbits, push-ins; where it holds.
   - **Colours** (sampled hex) and **fonts** (closest families; how emphasis is done).
   - Note watermarks/agency marks — never copy them.
3. Then map the reference's structure onto the client's product, *through the brief*: keep structure and energy, replace anything that clashes (hooks that imply claims, colour codings, imagery), and use the client's motif where the reference used its own.

## Writing the film's structure (`brand/STRUCTURE.md`)
- **Order = the product story.** A good default for SaaS: hook (the problem, in the brand's words) → brand reveal on the drop → the product surface (feed/dashboard) → the key feature → proof/evidence (linger here, often the breakdown) → secondary feature → the outcome/tagline → end card with URL + CTA.
- **Timing base**: bpm, music.start, beat length, downbeats; where drop/breakdown/return land.
- **Scene chain**: one row per scene with time and beat range, copy, what happens, the one camera move, and **Out → next** (the exact shape that carries over). Validate: scenes contiguous, each Out is the next In.
- **Beat map**: one line per scene, `b<n>` for every beat, downbeats in bold. Validate programmatically that 0…N−1 each appear once.
- **Cue list**: from the beat map — every click and every fast move gets a sound.
- **Content table**: every product string/image, verbatim, with its source. Missing content is an open question for the client, not something to invent.
- Lint the copy against the brief (banned words, exclamation marks, claims about planned features) before showing it.

## Formats
- Don't crop a 16:9 film to 9:16. Re-lay it out: stack headline above UI, "word / object / word" on three lines, larger type. Same beats.
- Shortening: remove whole scenes and re-chain (the previous Out must become the next In).

## Timing arithmetic worth remembering
- 120 BPM: beat 0.5 s, bar 2 s, 48 s = 96 beats = 24 bars.
- Typing: ~25–35 chars/s reads as typing; the last keystroke lands on the beat. Faster than ~3 chars/frame reads as a strobe — use a mask exit instead of deleting long lines.
- Floods: ~0.3 s, overscaled past the corners.
