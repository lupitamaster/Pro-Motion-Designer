# Where to look (phase 4) — references, components, FX, music, SFX, fonts

Recommend 5–8 that fit the brand, not the whole list. Licences change: always open the licence page and tell the user what it says before anything is downloaded or used commercially.

## Reference films and inspiration
- **Launch films of product-led brands** — Apple keynotes, Linear, Stripe, Vercel, Raycast, Arc/The Browser Company, Notion, Figma release videos (their sites/YouTube). Study pace, how UI is staged, how scenes hand off.
- **Screen Studio** (screen.studio) — the zoom-to-the-action screen-recording look many SaaS demos use.
- **Dribbble** (dribbble.com, search "product video", "saas motion", "UI animation") and **Behance** (behance.net, Motion Graphics) — stills and short loops from motion studios.
- **Awwwards** (awwwards.com) and **Godly** (godly.website) — current web motion and landing pages; good for transitions and type treatments.
- **Mobbin** (mobbin.com) — real app UI patterns, to stage believable product screens.
- **Communities to ask / browse:** r/motiondesign and r/AfterEffects (reddit.com), School of Motion (schoolofmotion.com) articles/community, Motionographer (motionographer.com) for studio work.
- Agency SaaS demo reels (many studios specialise in SaaS explainers) — useful to break down, never to copy branding.

## Components and FX (code)
- **GSAP** (gsap.com) — timelines, text splitting, morphing; now free for commercial use (check current terms). Drive it from `seek(t)` (paused timeline, `progress()`), never real time.
- **Motion** (motion.dev, ex Framer Motion) — springs and layout ideas; port the maths, keep frames pure.
- **Lottie / LottieFiles** (lottiefiles.com) and **Rive** (rive.app) — icon/illustration animations; seek them by frame.
- **Codrops** (tympanus.net/codrops) — well-explained web FX demos (text reveals, distortion, grain, transitions).
- **CodePen** (codepen.io) and **Shadertoy** (shadertoy.com) — FX prototypes; check each author's licence before reuse.
- **Remotion** (remotion.dev) — React video framework; an alternative to this studio. Its licence requires a company licence above a small team size — check before recommending.
- Icons: **Lucide** (lucide.dev), **Phosphor** (phosphoricons.com) — open licences; match the product's own icon set when possible.

## Music (≈120 BPM with a drop suits product films)
- **Mixkit** (mixkit.co/free-stock-music) — free licence; genre pages expose a waveform JSON per track (`waveformUrl`) you can screen for drops before downloading.
- **Pixabay Music** (pixabay.com/music) — free licence.
- **YouTube Audio Library** — free, some tracks need attribution.
- **Uppbeat** (uppbeat.io) — free tier with attribution.
- Paid, for campaigns: **Artlist**, **Musicbed**, **Epidemic Sound** (licences per channel/usage).

## SFX
- **Mixkit SFX** (mixkit.co/free-sound-effects) — whoosh, click, pop, chime, typing, impact; full WAVs at `.../sfx/<id>/<id>.wav` (some only have a preview MP3).
- **Freesound** (freesound.org) — huge, licence per sound (CC0 / CC-BY / CC-BY-NC — NC is not for commercial).
- **Pixabay SFX**, **ZapSplat** (zapsplat.com, attribution on the free tier).
- Always measure every SFX (`analyze_audio.py`) — names lie (a "riser" can be flat).

## Footage and stills (only when the film needs real-world texture)
- **Pexels** (pexels.com/videos), **Pixabay**, **Mixkit video** — free licences; avoid identifiable people/brands in commercial use unless released.

## Fonts
- **Google Fonts** (fonts.google.com) — OFL; download the full family from the google/fonts GitHub repo, not a site's subsetted webfont.
- **Fontshare** (fontshare.com) — free for commercial use (check per family).
- The brand's own licensed fonts — ask for the files and confirm the licence covers video.
