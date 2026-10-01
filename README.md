
# suno_packs

Open-source Suno AI song packs by [lulabubble](https://suno.com/@q1w2e3r4t05y06905).

This repository contains text-based packs for generative music on Suno AI. Each pack is a self-contained `.txt` file with a structure map, working lyrics, delivery/technique notes, and a plain-English reference layer for the model. The packs are licensed for reuse and remixing under CC BY 4.0.

No audio files are stored here. The published tracks live on Suno; each pack header links to its published generation.

## Remixers — no barriers

These packs are meant to be remixed. Covers, mashups, lyric swaps, cascade quality passes — all welcome. You do not need to ask, and you do not need to build a wall of links.

On Suno:

- Suno auto-links every Cover / Mashup to the original track.
- The original track page shows the author and links back to it. One click.
- The license is reachable from there — the pack header carries the license URI.
- For a quick lyric swap or a remix, **you do not need to paste any links at all**. The platform already shows the source.

Cascade remixes (cover of a cover, mashup of a mashup — the usual quality-pass chain):

- Suno may drop the auto-link somewhere down the chain.
- If that happens, use Suno's **Share short link** for the track you built on. It is short, it fits in lyrics, caption, or description, and it links back to the chain.
- That one short link is enough. Nothing longer is required.

Off-platform (YouTube, Bandcamp, anywhere else):

- Credit **lulabubble** and link the license:  
  https://creativecommons.org/licenses/by/4.0/
- That is the whole obligation. CC BY 4.0 allows commercial use too.

Short version: if you remixed it on Suno, you are already compliant. If you took it off-platform, credit + license link. If you lost the chain, drop the Suno share link.

## Repository layout

```text
suno_packs/
├── LICENSE
├── README.md
├── 0001_crimson_sunrise/
│   └── pack.txt
├── 0002_two_doors/
│   └── pack.txt
├── copy_and_check.sh
├── dump.sh
└── editor.sh
```

Packs are numbered in release order: `0001_...`, `0002_...`, etc.

## What is a pack?

A pack has three parts:

1. **HEADER** — license, repo link, published link, structure, remix rules, technique, timing. Metadata, not lyrics.
2. **WORKING LYRICS** — the actual lyrics and bracketed directions for Suno. This is the part you keep for a remix.
3. **APPENDIX** — principles for phonetics, safe variants, voice stacking, understatement, etc. Metadata, not lyrics.

When remixing, delete HEADER and APPENDIX. Keep WORKING LYRICS only.

### What goes in a pack — and what does not

A pack is a publishable artifact, not a working notebook. It carries a **minimal skeleton** of the things a reader needs to be self-contained: the remix line, the role line, the track metadata. Each of these has a **full version in this README**. The pack keeps the short form on purpose; the README keeps the long form. Do not expand the short form here, and do not copy the long form in.

The three things the pack carries minimally, with their full versions in this README:

1. **Remix skeleton.** One line — what to keep, what to delete, license name. Full version: "Remixers — no barriers" and "How to use a pack in Suno" in this README. Do not add link-pasting instructions, cascade handling, or attribution wording to the pack — those are README-only.

2. **Role line.** One line — Creator / Critic / Operator, named but not explained. Full version: "Make your own pack" in this README. Do not add role descriptions, workflow steps, or responsibilities to the pack.

3. **Track metadata.** License, repo, path, published link, structure, technique, notation, timing. This is the pack's own content and belongs here in full — but written for a reader of the track, not for the author of the process.

What never goes in a pack, in any amount:

- **Process notes.** Anything about the author's workflow: scope rules, compression policy, iteration numbers, test results, "operator sends Lyrics as-is", "test-1 showed", "this is a description not a command". Working notes live outside the repo.
- **Meta-pointers.** Cross-references like "target defined in APPENDIX", "see HEADER for timing", "as noted above". If a fact is worth stating, state it where it belongs. Pointers are clutter.

The test for any line in HEADER or APPENDIX: **is this the minimal skeleton of something that has a full version in this README, or is this process/meta?** If it is the minimal skeleton — keep it, do not expand it. If it is process or meta — remove it.

Before publishing a pack (filling the Published link), run a cleanup pass: read HEADER and APPENDIX line by line. Expand nothing, add nothing, only remove what fits the "never" list and what exceeds the minimal skeleton.

## How to use a pack in Suno

1. Open a `pack.txt`.
2. Copy the **WORKING LYRICS** section.
3. Paste it into Suno's lyric editor.
4. Set **Title** and **Style** separately in Suno. They are intentionally not stored in the pack.
5. Generate.

Bracketed text like `[Intro]` and `[whisper]` is direction, not sung lyrics. `[ref:]` lines are plain-English helpers, also not sung. If Suno sings them aloud, treat that as a test finding rather than a lyric.

## Make your own pack

The same format works for anyone. A pack is just text, and you can build one with a smart chatbot and a clear head.

The minimum setup is three roles — a small, manual agentic loop:

- **Creator** — first chat window of a smart chatbot (GPT, Kimi, Claude, whatever you prefer).
- **Critic** — a second, separate chat window of the same kind of chatbot. Its only job is to review.
- **Operator** — you. The only real person in the loop.

Creator and Critic are just two windows of a chatbot. They do not share memory, they do not talk to each other directly, and they have no responsibility for anything. The Operator is the bridge: reads one, writes to the other, and decides what actually happens.

The loop is simple:

1. Operator gives the pack to the Creator window. Roles and rules are already described inside the pack — no separate briefing needed.
2. Creator produces or revises lyrics, structure, techniques.
3. Operator hands the result to the Critic window. Critic reviews.
4. Operator relays the critique back to the Creator, or accepts it, or rejects it.
5. Operator runs the generation in Suno, listens, gives feedback, decides when the pack is done.

**The Operator carries the responsibility.** Not the chatbots. Every generation, every piece of feedback, every published pack is the Operator's call. The chatbots suggest; the Operator decides.

This is where critical thinking matters most. A pack is only as good as the human running the loop. The more the Operator stays awake — listens carefully, questions the critique, pushes back on the Creator, notices what a generation is really doing — the better the pack gets. Passive relaying produces mediocre packs. Active judgment produces good ones.

Start with one pack, one Creator window, one Critic window, and yourself. That is the whole framework.

## License

Unless otherwise noted, all lyrics and pack text in this repository are © 2026 lulabubble and licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**. See [LICENSE](LICENSE).

You may copy, modify, distribute, and use the material commercially, provided you give appropriate credit.

## Status

Published packs:

- `0001_crimson_sunrise` — published; link in pack header.
- `0002_two_doors` — published; link in pack header.

New packs are added as `0003`, `0004`, etc. Each pack header is the source of truth for its published link.

## Contact

- Suno: https://suno.com/@q1w2e3r4t05y06905
- GitHub: https://github.com/lulabubble/suno_packs

For corrections or questions, open an issue on GitHub.

## Author's internal tools (not part of the packs)

The shell scripts in the repository root are personal utilities used only by the author. They exist because the author often works from a phone in Termux, where this repository lives directly, and copies packs between a working directory and the repo. They are nothing more than convenience glue.

- `copy_and_check.sh` — copy a working pack into the current repo pack directory.
- `dump.sh` — dump git history and the LICENSE/pack diff.
- `editor.sh` — copy the current repo pack into a working directory for editing.

If you are here to read, reuse, or remix a pack, you can ignore this section entirely. Packs are plain text and require no scripts, no tooling, and no setup.

