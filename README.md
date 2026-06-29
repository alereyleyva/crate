# crate

crate is a Python CLI for finding mix points, structure, BPM and key in electronic tracks.

It analyzes audio files and exports:

- `track.analysis.json` for machines, matching engines and future embeddings.
- `track.report.md` for humans and direct LLM context.

The project is intentionally heuristic-first. Version `0.1.0` prioritizes useful, explainable reports over perfect DSP, key detection or vocal detection.

## Features

- Single-track and folder batch analysis.
- Parallel folder analysis with resumable outputs.
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
- `uv` for development and local project management
- macOS, Linux or Windows with a working Python environment
- Optional: `ffmpeg` if your local audio stack cannot decode a specific compressed format

Supported input extensions:

```text
.aif .aiff .flac .m4a .mp3 .ogg .wav
```

## Install From GitHub

For CLI usage, `uv tool install` is recommended because it installs the app in an isolated environment and exposes `crate` globally.

```bash
uv tool install git+https://github.com/<owner>/crate.git
```

Then run it from any folder:

```bash
crate analyze ./music/track.mp3 --out ./reports
```

Upgrade after pulling new commits or tags:

```bash
uv tool upgrade crate
```

Install a specific tag:

```bash
uv tool install git+https://github.com/<owner>/crate.git@v0.1.0
```

## Install For Development

```bash
git clone https://github.com/<owner>/crate.git
cd crate
uv sync --extra dev
```

Run tests:

```bash
uv run pytest
```

Run type checks:

```bash
uv run basedpyright
```

Run the CLI from the local environment:

```bash
uv run crate --help
```

## Quick Start

```bash
crate analyze ./audio/track.mp3 --out ./reports
```

During development, prefix commands with `uv run`:

```bash
uv run crate analyze ./audio/track.mp3 --out ./reports
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
crate analyze ./audio/track.mp3
```

Set output folder:

```bash
crate analyze ./audio/track.mp3 --out ./reports
```

Analyze a folder:

```bash
crate analyze ./audio-folder --out ./reports
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
crate analyze ./track.mp3 --json --no-markdown
```

Export only Markdown:

```bash
crate analyze ./track.mp3 --no-json --markdown
```

Change analysis frame rate:

```bash
crate analyze ./track.mp3 --frames-per-second 20
```

Analyze a large folder faster:

```bash
crate analyze ./audio-folder --out ./reports --fast --workers 4 --skip-existing
```

Performance-oriented options:

- `--workers 0` uses an automatic worker count for folders, capped conservatively at 4 by default. Use `--workers 8` or another explicit value if your machine has enough CPU and memory.
- `--fast` lowers analysis cost to `22050 Hz`, `10` frames per second and `2048` FFT while keeping STFT key estimation.
- `--sample-rate 22050` lowers decode/resampling cost. Use `--sample-rate 0` to keep the source rate.
- `--n-fft 2048` reduces spectral analysis cost compared with the default `4096`.
- `--key-mode stft` is the default fast key estimate. Use `--key-mode cqt` for a heavier estimate or `--key-mode none` to skip key estimation.
- `--skip-existing` skips tracks whose requested JSON/Markdown outputs already exist, which is useful when resuming large batches.

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

The schema is defined in `src/crate/schema.py`.

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
src/crate/
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
uv tool install git+https://github.com/<owner>/crate.git@v0.1.0
```

See `docs/releasing.md` for the full workflow.
