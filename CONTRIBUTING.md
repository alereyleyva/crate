# Contributing

## Development Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

## Test

```bash
.venv/bin/python -m pytest
```

## Run Locally

```bash
.venv/bin/groove-analyser analyze ./track.mp3 --out ./reports
```

## Guidelines

- Preserve the CLI command `groove-analyser analyze`.
- Preserve the top-level JSON schema unless intentionally versioning a breaking change.
- Keep normalized values clamped to `[0, 1]`.
- Avoid writing frame-by-frame arrays into the main JSON unless there is a clear use case.
- Prefer small, explainable heuristics over opaque models for v1.
- Add tests for schema, report generation and numeric edge cases when changing analysis logic.
