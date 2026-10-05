# Techniques

Companion reference for the suno_packs repository. Long-form. The packs stay minimal; this file carries the full descriptions. Nothing here is sung. Brackets and `[ref:]` are directions for the model, not lyrics.

## Pack-format short summary

```text
TECHNIQUES SUMMARY v1.0

HEADER
License: CC BY 4.0 — see LICENSE.
Repo: https://github.com/lulabubble/suno_packs
Path: TECHNIQUES.md
Scope: full technique reference. Not a pack. Not sung. No audio.
Packs keep the short form; this file keeps the long form.

Notation:
[brackets] = directions, not sung.
[ref:] = plain-English helper, not sung.
(vowel hums: oo, ah, mm, oh) = fillers, sung.
(words) = answering voice, verse only.
[spoken] = spoken. [hum] = hummed.

Core rule:
Compression lives in the bridge.
Fillers live everywhere except the bridge.
If the bridge gets fillers, it stops being fast.
If the verse loses the answering voice, it flattens.
If the outro concludes, it stops decaying.

LIST OF TECHNIQUES
1. Compression
2. Fillers
3. Bracketed directions
4. [ref:] reference layer
5. Spoken frame
6. Answering voice
7. Voice stacking
8. Wave
9. Chorus rewrite
10. After-bridge final chorus
11. Collapse
12. Understatement / decay
13. Drift
14. Diegetic silence / voice disappearance
15. Accent paradox
16. Phonetic safe variants
17. Timing targets
18. Remix-safe structure

APPENDIX
Full descriptions below. This summary is not a pack. Not sung. No audio.
```

## List of techniques

1. **Compression** — bridge-only syllable merge and vowel removal; makes the bridge accelerate.
2. **Fillers** — sung vowel hums `(oo)(ah)(mm)(oh)`; absent in bridge, present elsewhere.
3. **Bracketed directions** — `[Intro]`, `[whisper]`, `[belt]`; not sung.
4. **`[ref:]` reference layer** — plain-English line above a compressed line; not sung.
5. **Spoken frame** — spoken intro/outro that frames the song; dry, close-mic.
6. **Answering voice** — parenthetical second presence in verse; not an echo.
7. **Voice stacking** — pre-chorus builds by adding voices, not volume.
8. **Wave** — pre-chorus shape: build, pull back, release.
9. **Chorus rewrite** — chorus 2 keeps first lines, rewrites last lines.
10. **After-bridge final chorus** — verbatim chorus with changed delivery.
11. **Collapse** — final chorus peak drops into drone; thesis returns spoken.
12. **Understatement / decay** — outro decays; silence becomes content.
13. **Drift** — voice drifts into instrumental; accent dissolves last.
14. **Diegetic silence** — answering voice disappears; pause is a direction.
15. **Accent paradox** — one language, two worlds; coastal British vs neutral English.
16. **Phonetic safe variants** — restore shortest readable form if model glitches.
17. **Timing targets** — ~4:00; bridge ~0:30; FC ~0:40; outro ~0:25.
18. **Remix-safe structure** — HEADER / WORKING LYRICS / APPENDIX; remix keeps only WORKING LYRICS.

## Full reference

### Compression

**Purpose:** make the bridge accelerate.  
**Where:** bridge only.  
**Rules:** syllable merge; `-ing` → `-in`; `every` → `evry`; `and` → `an`; `of` → `o`; `is` → `'s`; drop `a`; aggressive vowel removal.  
**Never:** compress verses, pre-chorus, chorus, intro, or outro.  
**Remix knob:** slower remix — add fillers back into bridge; faster remix — remove more vowels.

### Fillers

**Purpose:** dreamy contrast, breath, slow-section texture.  
**Where:** intro, verse, pre-chorus, chorus, outro. Outro keeps fillers only on the first two lines in some packs.  
**Never:** bridge. Bridge without fillers is what makes it fast.  
**Notation:** `(oo)`, `(ah)`, `(mm)`, `(oh)` — sung.  
**Remix knob:** add or remove per section; never add to bridge unless slowing the bridge.

### Bracketed directions

**Purpose:** direct the model.  
**Examples:** `[Intro — slow, warm steam]`, `[whisper]`, `[belt]`, `[cut]`, `[pause]`.  
**Rule:** not sung. If a generation sings them aloud, treat it as a test finding, not a lyric.

### `[ref:]` reference layer

**Purpose:** give the plain-English intended words above a compressed line.  
**Rule:** not sung. Read across without pausing. The `[ref:]` line gives word breaks; the compressed line gives the rhythm.  
**Use:** bridge compression only, in these packs.

### Spoken frame

**Purpose:** frame the song as a story.  
**Where:** intro and/or outro.  
**Rules:** `[spoken]`, dry, close-mic, no reverb, no fillers.  
**Example:** `[spoken] Sit down. Let me tell you a story about me.`

### Answering voice

**Purpose:** a second, diegetic presence in the verse. It was in the room, remembers it, knows more than the lead did then.  
**Notation:** `(words)` in verse only.  
**Rules:** answers, extends, or contradicts — never repeats the lead verbatim. One to four words per answer. Different register or pan.  
**Failure mode:** if it flattens into the lead, the technique fails.  
**Variant:** algorithmic/flat voice in 0004; cold therapist voice in 0005.

### Voice stacking

**Purpose:** build the pre-chorus by adding voices, not volume.  
**Rules:** line 1 = one voice; each next line adds distinct voices by register, pan, or echo; last line = full unison stack. Never double the lead verbatim.  
**Forms:** accumulation `1 → 2 → 3 → all`; lead-with-echo `lead → distant echo → closer echo with harmony → unison lock`.  
**Lives in:** the lyrics, not in a separate list.

### Wave

**Purpose:** pre-chorus shape that rises and retreats before landing.  
**Rules:** build → pull back → release. Line 3 retreats to one voice, closer; line 4 lands.  
**Used in:** `0004_ear_to_the_shell`.

### Chorus rewrite

**Purpose:** show that the narrator has changed.  
**Rules:** first two lines verbatim; last two rewritten. Delivery unchanged — the change is in the text alone.  
**Used in:** `0005_twice_daily`.

### After-bridge final chorus

**Purpose:** peak.  
**Rules:** repeats earlier choruses verbatim. Only delivery changes: belt from the first line, added harmony, layered vocals.  
**Used in:** 0002, 0003, 0004, 0005.

### Collapse

**Purpose:** the peak does not resolve; it collapses into the thesis.  
**Rules:** belts from line 1; then drop — drums cut, drone only; thesis returns spoken, quiet, cold. Never lengthen the drop; silence inside the drone is the point.  
**Used in:** `0005_twice_daily`.

### Understatement / decay

**Purpose:** outro does not conclude — it decays.  
**Rules:** voice stops finishing words, lines, thoughts. Silence becomes content. Cut where the voice would run out. Never lengthen. Fragments return smaller. Read as one continuous decay.  
**Used in:** 0002, 0003, 0005.

### Drift

**Purpose:** outro floats into the instrumental.  
**Rules:** voice drifts into the instrumental; instrumental fills the gaps; accent dissolves last. Never lengthen.  
**Used in:** `0004_ear_to_the_shell`.

### Diegetic silence / voice disappearance

**Purpose:** mark a change in who is speaking.  
**Rules:** `[silence — answering voice gone]` is a direction, not a lyric. After that, the narrator speaks in that voice's register — same tone, new mouth.  
**Used in:** `0005_twice_daily`.

### Accent paradox

**Purpose:** one language, two worlds.  
**Rules:** coastal British = real sea; neutral English = digital harbor. The shift between sections is the technique. Directive vs description: the model executes directive words in the lyric (`neutral`); descriptive neologisms live in the appendix only (`placeless`). A descriptive word in a directive slot reads as noise.  
**Nudge:** respell where British and American differ (`wata`, `learnt`, `lido`); `harbor` as counter-marker.  
**Used in:** `0004_ear_to_the_shell`.

### Phonetic safe variants

**Purpose:** fix glitches without changing rhythm.  
**Rules:** compressed lines read as one continuous phrase. Removed vowels are silent; consonants glue to the next word. Merge only to save a syllable. Function words (`and`, `then`, `I`, `am`) stay separate. Merged form must not be a different English word; if it is, drop the leading vowel (`a version` → `vrsion`).  
**Glitch fix:** restore the shortest readable form (`is` → `'s` → `s`; `every` → `evry`). Keep syllable count and stress pattern. Never lengthen the rhythm. Unzip one letter at a time until the glitch clears.

### Timing targets

**Default:** ~4:00 total. Bridge ~0:30 (~12.5%). Final chorus ~0:40, peak. Outro ~0:25, decay.  
**Variant:** 0004 outro ~0:35.  
**Rule:** do not change timing without changing the technique that fills it.

### Remix-safe structure

**Parts:** HEADER / WORKING LYRICS / APPENDIX.  
**Remix:** delete HEADER, delete APPENDIX, keep WORKING LYRICS only.  
**License:** CC BY 4.0. On-platform, Suno auto-links Cover/Mashup to the original. Off-platform: credit `lulabubble` + link the license.  
**Cascade:** if Suno drops the auto-link, use Suno's Share short link.

## Pack usage matrix

| Technique | 0001 | 0002 | 0003 | 0004 | 0005 |
|---|---:|:---:|:---:|:---:|:---:|
| Compression | ✓ | ✓ | ✓ | ✓ | ✓ |
| Fillers except bridge | ✓ | ✓ | ✓ | ✓ | ✓ |
| Bracketed directions | ✓ | ✓ | ✓ | ✓ | ✓ |
| `[ref:]` | ✓ | ✓ | ✓ | ✓ | ✓ |
| Spoken frame | — | — | ✓ | ✓ | ✓ |
| Answering voice | — | — | ✓ | ✓ | ✓ |
| Voice stacking | — | ✓ | ✓ | ✓ | ✓ |
| Wave | — | — | — | ✓ | — |
| Chorus rewrite | — | — | — | — | ✓ |
| After-bridge FC | — | ✓ | ✓ | ✓ | ✓ |
| Collapse | — | — | — | — | ✓ |
| Understatement / decay | — | ✓ | ✓ | — | ✓ |
| Drift | — | — | — | ✓ | — |
| Diegetic silence | — | — | — | — | ✓ |
| Accent paradox | — | — | — | ✓ | — |
| Phonetic safe variants | ✓ | ✓ | ✓ | ✓ | ✓ |
| Timing targets | ✓ | ✓ | ✓ | ✓ | ✓ |
| Remix-safe structure | ✓ | ✓ | ✓ | ✓ | ✓ |

## Remix notes

- Keep WORKING LYRICS. Delete HEADER and APPENDIX.
- Do not add fillers to the bridge unless you are slowing it down.
- Do not remove the answering voice from the verse unless you want the verse to flatten.
- Do not let the outro conclude. Let it decay or drift.
- If a model sings `[brackets]` or `[ref:]`, that is a test finding — fix it when it happens, not preemptively.
- Title and Style are handed over separately at generation time. They are not stored in the pack.
