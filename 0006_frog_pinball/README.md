# 0006 Frog Pinball

First pack in this repo to bundle **runnable Python source** together with the cover pack. The instrumental is generated from `frog_pinball_ukg_v5.py` (numpy + scipy, no external samples), and `cover.txt` is written against that exact source — bars, positions, pitches, effects all trace back to the code, not to a remembered reference.

## Files

- **cover.txt** — three copy-paste fields for Suno cover generation: title, style (~890 chars), lyrics (per-bar structure map with bracketed directions).
- **frog_pinball_ukg_v5.py** — instrumental generator. 42 bars, 132 -> 144 -> 132 BPM pivot, A minor Aeolian with Dorian F# color, 12-bit SP-1200 chain, 8-bit arcade accents on a separate 7.5 kHz chain, pearl techniques (Cantor pairing, HRTF, bells at birth/assembly/dissolve, breath envelope, synthetic IR reverb post-SP-1200).
- **published.txt** — Suno short link plus the style block Suno returned for the variation that was selected for publication.

## How to use

1. Run `python3 frog_pinball_ukg_v5.py` to regenerate the source instrumental.
2. Open `cover.txt`, copy each of the three fields into Suno's title / style / lyrics.
3. Generate a cover against the source instrumental.

## Why this pack is different

Previous packs (0001-0005) are text-only: structure, working lyrics, appendix. This pack pairs a cover pack with reproducible source. The Python file is the ground truth for every bar, beat position, pitch and effect in `cover.txt` — no guessing, no drift between source and cover.

## Published

https://suno.com/s/FuUUGS53ECdnHgLa

## Discord blurb (copy the line below)

Frog Pinball — 12-bit deconstructed UKG with 8-bit arcade accents, frog-hop kicks, croaking elastic sub, square-wave pinball arpeggio, dub-reggae chord stabs, bells and pinball FX. 132 -> 144 BPM. Generated from Python source, bundled in the pack. https://suno.com/s/FuUUGS53ECdnHgLa
