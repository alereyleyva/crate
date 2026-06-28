# Architecture

Groove Analyser is organized around a small analysis pipeline with explicit module responsibilities.

## Flow

```text
CLI input
  -> load audio
  -> compute band curves
  -> estimate beats and bars
  -> compute global and bar features
  -> detect sections
  -> detect mix points
  -> build LLM summary
  -> validate Pydantic schema
  -> write JSON and Markdown
```

## Modules

- `cli.py`: parses command-line options and displays progress.
- `config.py`: centralizes analysis knobs such as frame rate, target sample rate and phrase length.
- `pipeline.py`: coordinates the full track analysis and returns a validated `TrackAnalysis` object.
- `audio.py`: loads audio with `librosa`, converts to mono and captures basic metadata.
- `bands.py`: computes STFT energy for six named frequency bands and low/mid/high aggregates.
- `beats.py`: estimates BPM, normalizes obvious DJ half-time/double-time tempos and infers 4/4 bars.
- `features.py`: computes spectral curves, global descriptors and per-bar features.
- `keys.py`: estimates key and Camelot from chroma profiles.
- `sections.py`: groups bars into phrase-sized regions and assigns heuristic section labels.
- `mixpoints.py`: scores mixability, high-risk regions and LLM-facing summary text.
- `schema.py`: defines the stable JSON contract with Pydantic.
- `report.py`: renders the Markdown report.
- `output.py`: writes JSON, Markdown and batch index files.
- `utils.py`: contains numeric safety, normalization, time formatting and audio file discovery helpers.

## Design Principles

- Keep DSP code separate from report generation.
- Keep JSON schema stable and explicit.
- Clamp normalized values to `[0, 1]`.
- Avoid `NaN` and infinity in JSON output.
- Prefer bar/section summaries over long frame-level arrays.
- Use explainable heuristics before introducing heavier ML dependencies.

## Data Contract

The public output contract is `TrackAnalysis` in `schema.py`. Any future changes should preserve top-level keys where possible:

```text
version
track
bands
sections
mix_points
llm
```

When making breaking schema changes, bump the project version and document the change.
