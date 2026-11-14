# #BandDecision — DJ REZRXTION™ Suno lyric formatting and producer-tag convention

**Decision ID:** BD-MUSIC-001  
**Date:** 2026-11-14  
**Status:** OWNER-APPROVED CREATIVE RULE — documentation only  
**Owner:** DJ RezrXtion / S.A.R.A. Studio music creation and lyric preparation  
**Authority:** This document governs authored Suno-facing lyric text and style prompts. It is not a new SongSpec, ProjectRevision, LyricTimelineRevision, renderer, audio artifact, or alternate source of project truth.

## Decision

**Return to our original bracketed performance-direction convention, with ONE exception: the exact audible DJ producer tag is written outside brackets.**

- **Producer tag (vocalized text):** write `D-D-D-DJ RESURRECTION!` on its own unbracketed lyric line, following a bracketed performance cue. It may appear in the intro, outro, instrumental breaks, or selective transitions. Maintain artist name **DJ REZRXTION™** in titles/metadata; **RESURRECTION** is the phonetic performance tag.
- **DJ scratches, chops, spins, skips, samples, beat-juggling and effect instructions:** remain entirely inside square brackets, including named scratch words: `[DJ scratches: HERE / THERE; left-to-right]`. This is the user's preferred authoring convention even when a scratch instruction contains words.
- **Hypeman calls and shout-outs:** remain bracketed, including words intended as performance directions: `[HYPE, low] DON'T OPEN THAT WINDOW!` or `[HYPE, dry: RUN IT BACK!]`. Do **not** expand these into standalone lyric lines by default.
- **Arrangement, production, role and sound design:** remain bracketed: `[CHORUS — huge CLEAN sung; club-rock]`, `[DJ backspin; sub returns]`, `[FEMALE ALTO — haunting wordless harmony]`.
- **Actual lead lyrics and deliberately featured spoken/sung dialogue:** go outside brackets, with a role/performance cue in brackets immediately before them as needed.
- **No blanket rewrite of all bracketed material into bare lyrics.** The earlier attempt to place HERE/THERE, NOW/THEN, and all hype words outside brackets was explicitly rejected by the owner.
- **No retroactive modification of completed masters without an explicit targeted change request.** Default applies to new songs and requested revisions.

## Preferred copy/paste pattern

```text
[INTRO — vinyl texture, sub enters]
[DJ back-cue, deep rhythmic scratch]
D-D-D-DJ RESURRECTION!
[DJ chirps: HERE / THERE; opposite decks]
[HYPE, low] DON'T OPEN THAT WINDOW!
[MALE, spoken]
One day. That's all I'm showing you.

[VERSE 1 — methodical, precise rap]
My first complete lyric line,
My second complete lyric line.
[DJ cuts: LINE / TIME; guitar replies]

[BRIDGE — heartbeat, piano]
[FEMALE ALTO, intimate melodic reply]
You can choose where you stand.

[OUTRO — needle slowing]
[DJ whispered back-cue]
D-D-D-DJ RESURRECTION...
[Needle lift]
```

## Sonic invariants

1. **Song-specific identity:** vary tag treatment, scratch vocabulary, arrangement and placement; avoid copying the same intro mechanically into every track.
2. **DJ as performer:** real performance concepts—chirps, flares, crabs, transformers, backspins, crossfader percussion, beat juggling, guitar replies and intentional timing—rather than purely decorative FX.
3. **Clear lead:** scratches and hype mostly occupy intentional gaps; do not mask rhymes, consonants, or essential dialogue.
4. **Production tone:** polished studio audio by default; no live-crowd wash or generic audience noise unless expressly requested.
5. **Rap standard:** methodical melodic technical flow; closed rhymes, judicious multis, natural breath and perfectly intelligible wording. No forced speed or accent.
6. **Suno-ready boundaries:** final complete Lyrics ≤5,000 Unicode code points, Styles ≤1,000; repeat full hooks, count exact final text programmatically. Text-limit PASS is not evidence of audio or vocal-role PASS.

## Why the exception exists

In practice, Suno can interpret `[DJ back-cue: D-D-DJ RESURRECTION]` as non-vocal direction, skipping the audible producer tag. Moving **only the tag's actual words** outside brackets increases the likelihood of their being performed. Bracketed scratches/hype remain the creative notation requested by the artist.

**No Suno parser contract or guarantee is claimed.** A model may ignore a cue or treat bracketed words as vocals. For exact producer-tag pronunciation, placement and scratching, use a lawful pre-recorded tag/sample and section editing in a supported production workflow; preserve provenance.

## QA / review checklist

- [ ] Unbracketed `D-D-D-DJ RESURRECTION!` present where an audible tag is wanted
- [ ] Intro/outro/tag cues bracketed; tag words themselves unbracketed
- [ ] Scratch names and hypeman shout-outs stay bracketed by default
- [ ] Main lyrics and featured dialogue unbracketed under role cues
- [ ] No unsolicited bracket-format conversion
- [ ] Rhymes, word clarity and DJ gap timing reviewed
- [ ] Hooks fully repeated; final Unicode limits programmatically checked
- [ ] No fabricated render, listening, role separation or production certification

## Scope and governance

**SOURCE → AUTHORING RULE → REVIEWED TEXT → RENDERED AUDIO → AUDITION → CREATIVE APPROVAL** remain distinct gates. This decision is documentation for music creators and assistants, not a claim about production runtime behavior.

**One music owner:** `justinbusiness461-lab/SARA_studio`. Cinema in `dj_rezrxtion` consumes accepted music authority but does not own this lyric formatting law. Existing authoritative project/revision and audio artifacts remain unchanged.

**Owner wording that triggered this decision:** “Go back to how we were doing it before ... leave the D-D-D-DJ RESURRECTION out of the brackets ... the shout outs, the hypemen ... can still be in the brackets ... Only put what we want to be actual audible words that are said out loud outside of the brackets ... Like the DJ name.”

**Decision in one line:** **PRODUCER TAG OUTSIDE. DJ/HYPE/DIRECTION BRACKETS STAY.**
