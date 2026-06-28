from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from groove_analyser.pipeline import analyze_track
from groove_analyser.report import render_markdown
from groove_analyser.utils import audio_files_in, format_time


app = typer.Typer(help="Groove Analyser: LLM-friendly music analysis for DJ-oriented tracks.")
console = Console()


@app.callback()
def main() -> None:
    """Groove Analyser command group."""


@app.command()
def analyze(
    input_path: Annotated[Path, typer.Argument(exists=True, readable=True, help="Audio file or folder to analyze.")],
    out: Annotated[Path, typer.Option("--out", "-o", help="Output directory.")] = Path("./reports"),
    export_json: Annotated[bool, typer.Option("--json/--no-json", help="Write JSON analysis.")] = True,
    export_markdown: Annotated[bool, typer.Option("--markdown/--no-markdown", help="Write Markdown report.")] = True,
    frames_per_second: Annotated[int, typer.Option("--frames-per-second", min=1, max=100, help="Analysis frame rate.")] = 20,
) -> None:
    files = audio_files_in(input_path)
    if not files:
        raise typer.BadParameter("No supported audio files found.")
    if not export_json and not export_markdown:
        raise typer.BadParameter("At least one output format must be enabled.")

    out.mkdir(parents=True, exist_ok=True)
    batch_mode = input_path.is_dir() or len(files) > 1
    track_out = out / "tracks" if batch_mode else out
    track_out.mkdir(parents=True, exist_ok=True)
    index_entries: list[dict[str, str]] = []

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        for file in files:
            task = progress.add_task(f"Analyzing {file.name}", total=None)
            analysis = analyze_track(file, frames_per_second=frames_per_second)
            written = _write_outputs(analysis, track_out, export_json, export_markdown)
            index_entries.append({"filename": file.name, **written})
            progress.update(task, description=f"Analyzed {file.name}")

    if batch_mode:
        index_path = out / "index.json"
        index_path.write_text(json.dumps({"tracks": index_entries}, indent=2), encoding="utf-8")
        console.print(f"Wrote index: [green]{index_path}[/green]")

    for entry in index_entries:
        console.print(f"Analyzed [bold]{entry['filename']}[/bold]")
        if "json" in entry:
            console.print(f"JSON: [green]{entry['json']}[/green]")
        if "markdown" in entry:
            console.print(f"Markdown: [green]{entry['markdown']}[/green]")


def _write_outputs(analysis, out: Path, export_json: bool, export_markdown: bool) -> dict[str, str]:
    stem = Path(analysis.track.filename).stem
    written: dict[str, str] = {}
    if export_json:
        json_path = out / f"{stem}.analysis.json"
        json_path.write_text(analysis.model_dump_json(by_alias=True, indent=2), encoding="utf-8")
        written["json"] = str(json_path)
    if export_markdown:
        report_path = out / f"{stem}.report.md"
        report_path.write_text(render_markdown(analysis), encoding="utf-8")
        written["markdown"] = str(report_path)
    console.print(
        f"Duration: {format_time(analysis.track.duration_seconds)} | "
        f"Sample rate: {analysis.track.sample_rate} Hz | "
        f"Estimated BPM: {analysis.global_.bpm:.1f} | "
        f"Sections: {', '.join(section.label for section in analysis.sections) or 'none'}"
    )
    return written


if __name__ == "__main__":
    app()
