# Releasing And Installing

This project can be installed directly from GitHub without publishing to PyPI.

## Prepare The Repo

Run tests before tagging:

```bash
uv run pytest
uv run basedpyright
```

Optionally test against a local audio file:

```bash
uv run crate analyze ./music/example.mp3 --out ./reports-test
```

Do not commit local audio files, generated reports or virtual environments. They are ignored by `.gitignore`.

## Create A Tag

```bash
git tag v0.1.0
git push origin v0.1.0
```

## Install With uv

Recommended:

```bash
uv tool install git+https://github.com/<owner>/crate.git@v0.1.0
```

Use from any folder:

```bash
crate analyze ./track.mp3 --out ./reports
```

Upgrade:

```bash
uv tool upgrade crate
```

Reinstall a specific version:

```bash
uv tool uninstall crate
uv tool install git+https://github.com/<owner>/crate.git@v0.1.0
```

## Install With pipx Or pip

Use this only if you are not using `uv`.

With `pipx`:

```bash
pipx install git+https://github.com/<owner>/crate.git@v0.1.0
```

Inside a specific virtualenv:

```bash
python -m pip install git+https://github.com/<owner>/crate.git@v0.1.0
```

## Versioning

For now, use semantic version tags:

```text
v0.1.0
v0.2.0
v1.0.0
```

Keep `pyproject.toml` and `src/crate/__init__.py` in sync when bumping versions.
