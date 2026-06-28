# Groove Analyser

Groove Analyser is a Python CLI for producing LLM-friendly musical analysis reports for DJ-oriented electronic music.

It analyzes audio files and exports:

- `track.analysis.json` for machines, matching engines and future embeddings.
- `track.report.md` for humans and direct LLM context.

The project is intentionally heuristic-first. Version `0.1.0` prioritizes useful, explainable reports over perfect DSP, key detection or vocal detection.

## Features

- Single-track and folder batch analysis.
- JSON output validated with Pydantic.
- Markdown reports designed for human review and LLM context.
- Metadata extraction: filename, path, duration, sample rate and channels.
- Global musical features: BPM, key estimate, Camelot estimate, energy, bass weight, brightness, percussiveness, dynamic range and vocal presence estimate.
- Spectral descriptors: centroid, bandwidth, rolloff, flatness, RMS and zero-crossing rate.
- Six-band spectral analysis plus low/mid/high summaries.
- Beat grid and 4/4 bar inference.
- Bar-level energy, bands, onset density, chroma and vocal presence estimate.
- Heuristic sections: intro, groove, breakdown, build, drop, outro and unknown.
- Mix-in, mix-out, safe loop and high-risk region recommendations.

## Requirements

- Python `>=3.11`
- macOS, Linux or Windows with a working Python environment
- Optional: `ffmpeg` if your local audio stack cannot decode a specific compressed format

Supported input extensions:

```text
.aif .aiff .flac .m4a .mp3 .ogg .wav
```

## Install From GitHub

For CLI usage, `pipx` is recommended because it installs the app in an isolated environment and exposes `groove-analyser` globally.

```bash
pipx install git+https://github.com/<owner>/groove-analyser.git
```

Then run it from any folder:

```bash
groove-analyser analyze ./music/track.mp3 --out ./reports
```

Upgrade after pulling new commits or tags:

```bash
pipx upgrade groove-analyser
```

Install a specific tag:

```bash
pipx install git+https://github.com/<owner>/groove-analyser.git@v0.1.0
```

## Install For Development

```bash
git clone https://github.com/<owner>/groove-analyser.git
cd groove-analyser
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

Run tests:

```bash
.venv/bin/python -m pytest
```

Run the CLI from the local virtualenv:

```bash
.venv/bin/groove-analyser --help
```

## Quick Start

```bash
groove-analyser analyze ./audio/track.mp3 --out ./reports
```

This creates:

```text
reports/
  track.analysis.json
  track.report.md
```

## CLI Usage

Analyze a single file:

```bash
groove-analyser analyze ./audio/track.mp3
```

Set output folder:

```bash
groove-analyser analyze ./audio/track.mp3 --out ./reports
```

Analyze a folder:

```bash
groove-analyser analyze ./audio-folder --out ./reports
```

Folder mode creates:

```text
reports/
  index.json
  tracks/
    track-001.analysis.json
    track-001.report.md
    track-002.analysis.json
    track-002.report.md
```

Export only JSON:

```bash
groove-analyser analyze ./track.mp3 --json --no-markdown
```

Export only Markdown:

```bash
groove-analyser analyze ./track.mp3 --no-json --markdown
```

Change analysis frame rate:

```bash
groove-analyser analyze ./track.mp3 --frames-per-second 20
```

## Output Files

### JSON

The JSON output is intended for machines, matching engines and future embeddings. Top-level sections:

```text
version
track
global
bands
timeline
sections
mix_points
llm
```

The schema is defined in `src/groove_analyser/schema.py`.

### Markdown

The Markdown output is intended for human review and LLM context. It includes:

- Track metadata and global features.
- High-level summary.
- Section table.
- Mix-in and mix-out recommendations.
- Matching notes.
- Risk notes.
- LLM summary paragraph.

## Important Caveats

- BPM is estimated and then normalized toward DJ-oriented ranges when obvious half-time/double-time detections occur.
- Key and Camelot are heuristic estimates from chroma, not professional-grade harmonic analysis.
- `vocal_presence_estimate` is a midrange/percussiveness heuristic, not a vocal detector.
- Section labels and mix points are v1 heuristics intended to be useful and debuggable, not definitive annotations.

## Project Layout

```text
src/groove_analyser/
  cli.py          CLI entrypoint
  config.py       Analysis configuration
  pipeline.py     End-to-end analysis orchestration
  audio.py        Audio loading
  bands.py        STFT band analysis
  beats.py        Tempo, beat and bar inference
  features.py     Spectral/global/bar features
  keys.py         Key and Camelot estimation
  sections.py     Section detection
  mixpoints.py    Mixability and LLM summary heuristics
  output.py       JSON/Markdown writing
  report.py       Markdown rendering
  schema.py       Pydantic output schema
  utils.py        Numeric and formatting helpers
```

More detail is available in `docs/architecture.md`.

## Publish From GitHub

1. Push this repo to GitHub.
2. Create a version tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

3. Install from another machine or folder:

```bash
pipx install git+https://github.com/<owner>/groove-analyser.git@v0.1.0
```

See `docs/releasing.md` for the full workflow.
