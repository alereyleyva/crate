# Groove Analyser

Groove Analyser is a Python CLI for producing LLM-friendly musical analysis reports for DJ-oriented electronic music.

It analyzes audio files and exports:

- `track.analysis.json` for machines, matching engines and future embeddings.
- `track.report.md` for humans and direct LLM context.

## Install

```bash
pip install -e .
```

## Usage

```bash
groove-analyser analyze ./audio/track.mp3 --out ./reports
```

Batch mode:

```bash
groove-analyser analyze ./audio-folder --out ./reports
```

Export only JSON or Markdown:

```bash
groove-analyser analyze ./track.mp3 --json --no-markdown
groove-analyser analyze ./track.mp3 --no-json --markdown
```

## Scope

Version 0.1.0 prioritizes explainable heuristics over complex ML. Key and vocal presence are estimates, not definitive detections.
