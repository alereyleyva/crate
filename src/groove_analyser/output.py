from __future__ import annotations

import json
from pathlib import Path

from groove_analyser.report import render_markdown
from groove_analyser.schema import TrackAnalysis


def write_track_outputs(
    analysis: TrackAnalysis,
    out: Path,
    export_json: bool = True,
    export_markdown: bool = True,
) -> dict[str, str]:
    out.mkdir(parents=True, exist_ok=True)
    stem = Path(analysis.track.filename).stem
    written: dict[str, str] = {}

    if export_json:
        json_path = out / f"{stem}.analysis.json"
        _ = json_path.write_text(analysis.model_dump_json(by_alias=True, indent=2), encoding="utf-8")
        written["json"] = str(json_path)

    if export_markdown:
        report_path = out / f"{stem}.report.md"
        _ = report_path.write_text(render_markdown(analysis), encoding="utf-8")
        written["markdown"] = str(report_path)

    return written


def write_batch_index(out: Path, entries: list[dict[str, str]]) -> Path:
    index_path = out / "index.json"
    _ = index_path.write_text(json.dumps({"tracks": entries}, indent=2), encoding="utf-8")
    return index_path
