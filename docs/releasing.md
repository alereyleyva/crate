# Releasing And Installing

This project can be installed directly from GitHub without publishing to PyPI.

## Prepare The Repo

Run tests before tagging:

```bash
.venv/bin/python -m pytest
```

Optionally test against a local audio file:

```bash
.venv/bin/groove-analyser analyze ./music/example.mp3 --out ./reports-test
```

Do not commit local audio files, generated reports or virtual environments. They are ignored by `.gitignore`.

## Create A Tag

```bash
git tag v0.1.0
git push origin v0.1.0
```

## Install With pipx

Recommended:

```bash
pipx install git+https://github.com/<owner>/groove-analyser.git@v0.1.0
```

Use from any folder:

```bash
groove-analyser analyze ./track.mp3 --out ./reports
```

Upgrade:

```bash
pipx upgrade groove-analyser
```

Reinstall a specific version:

```bash
pipx uninstall groove-analyser
pipx install git+https://github.com/<owner>/groove-analyser.git@v0.1.0
```

## Install With pip

Use this if you want the CLI inside a specific virtualenv:

```bash
python -m pip install git+https://github.com/<owner>/groove-analyser.git@v0.1.0
```

## Versioning

For now, use semantic version tags:

```text
v0.1.0
v0.2.0
v1.0.0
```

Keep `pyproject.toml` and `src/groove_analyser/__init__.py` in sync when bumping versions.
