from __future__ import annotations

import json
from pathlib import Path

from crate.report import render_markdown
from crate.schema import TrackAnalysis


def track_output_paths(
    filename: str,
    out: Path,
    export_json: bool = True,
    export_markdown: bool = True,
) -> dict[str, Path]:
    stem = Path(filename).stem
    paths: dict[str, Path] = {}
    if export_json:
        paths["json"] = out / f"{stem}.analysis.json"
    if export_markdown:
        paths["markdown"] = out / f"{stem}.report.md"
    return paths


def existing_track_outputs(
    filename: str,
    out: Path,
    export_json: bool = True,
    export_markdown: bool = True,
) -> dict[str, str] | None:
    paths = track_output_paths(filename, out, export_json, export_markdown)
    if not paths or not all(path.exists() for path in paths.values()):
        return None
    return {name: str(path) for name, path in paths.items()}


def write_track_outputs(
    analysis: TrackAnalysis,
    out: Path,
    export_json: bool = True,
    export_markdown: bool = True,
) -> dict[str, str]:
    out.mkdir(parents=True, exist_ok=True)
    paths = track_output_paths(analysis.track.filename, out, export_json, export_markdown)
    written: dict[str, str] = {}

    json_path = paths.get("json")
    if json_path is not None:
        _ = json_path.write_text(analysis.model_dump_json(by_alias=True, indent=2), encoding="utf-8")
        written["json"] = str(json_path)

    report_path = paths.get("markdown")
    if report_path is not None:
        _ = report_path.write_text(render_markdown(analysis), encoding="utf-8")
        written["markdown"] = str(report_path)

    return written


def write_batch_index(out: Path, entries: list[dict[str, str]]) -> Path:
    index_path = out / "index.json"
    _ = index_path.write_text(json.dumps({"tracks": entries}, indent=2), encoding="utf-8")
    return index_path
