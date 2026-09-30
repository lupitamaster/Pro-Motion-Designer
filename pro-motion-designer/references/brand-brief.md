# Brand brief (phase 3)

The brief is the film's rulebook: what can be claimed, how the brand speaks, what it never does, and the tokens every frame uses. Template: `brand/BRIEF.md`.

## If they already have one
- Keep their words. Normalise into the template's sections so later phases can find things (especially *today vs planned* and *don'ts*).
- When the user later corrects something (e.g. "the web is already public"), add it to the **Updates** block at the top and to your memory, so nobody reverts to the old text.
- Check the brief against reality when you can (the live site, the product): if they conflict, ask which wins.

## If they don't — draft it
1. **Website first.** Pull real tokens from the site instead of eyeballing screenshots:
   - download the HTML and its CSS (curl), grep `font-family`, `@font-face`, `--*` custom properties and hex colours; the font file names under `/_next/static/media/` or similar name the families;
   - note light *and* dark tokens if the site has a theme toggle;
   - read the hero, features and FAQ copy for voice, claims and vocabulary.
2. **Product.** Screens, flows, the words the UI uses (these are the verbatim strings you'll show).
3. **Interview (short).** Personality in 3 adjectives, brands it should feel like, the one accent colour, words/claims to avoid, stage (what's public), the name's meaning and any reading to avoid.
4. Mark everything you inferred as *(inferred)*; get it confirmed.

## Must-haves before moving on
- One accent colour (+ a darker variant for text on light), light/dark backgrounds, ink.
- Display, UI and data/mono faces — with licences. If a font isn't installable/licensable for video, pick the closest open alternative and say so.
- A **motif**: one recurring shape the film can build scenes out of (a dot/period, a cursor, a card, the logo's mark). It gives the "every scene comes out of the last" rule something to hold on to — and check it can't be misread (e.g. a dot "in the middle" of a left–right axis reads as political centre).
- **Today vs planned** list. Only today's features can be shown as existing.
- **Don'ts** → `project.json → brand_lint.banned` (words), plus the non-lintable ones (imagery, colour codings, claims) written clearly for the human checklist.
- Voice rules for on-screen copy: language/variant, person, case, punctuation.

## Common traps (seen in real productions)
- A reference video's hook ("Still doing X manually?") can imply something about competitors or the press that the brand can't say — rewrite hooks to the brand's actual problem statement.
- Real press photos / politicians in "example content" read as endorsement; use the product's own imagery and neutral examples.
- A tick/check next to a third party reads as "trusted"; a traffic-light palette reads as a judgement. Use them only if the brand means that.
- "Available now" / CTA copy must match the product's real stage (and where the CTA actually lands — e.g. an invite-only login).
