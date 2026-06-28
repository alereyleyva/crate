from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from groove_analyser.config import AnalysisConfig
from groove_analyser.output import write_batch_index, write_track_outputs
from groove_analyser.pipeline import analyze_track
from groove_analyser.schema import TrackAnalysis
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
    config = AnalysisConfig(frames_per_second=frames_per_second)

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        for file in files:
            task = progress.add_task(f"Analyzing {file.name}", total=None)
            analysis = analyze_track(file, config=config)
            written = write_track_outputs(analysis, track_out, export_json, export_markdown)
            index_entries.append({"filename": file.name, **written})
            _print_analysis_summary(analysis)
            progress.update(task, description=f"Analyzed {file.name}")

    if batch_mode:
        index_path = write_batch_index(out, index_entries)
        console.print(f"Wrote index: [green]{index_path}[/green]")

    for entry in index_entries:
        console.print(f"Analyzed [bold]{entry['filename']}[/bold]")
        if "json" in entry:
            console.print(f"JSON: [green]{entry['json']}[/green]")
        if "markdown" in entry:
            console.print(f"Markdown: [green]{entry['markdown']}[/green]")


def _print_analysis_summary(analysis: TrackAnalysis) -> None:
    console.print(
        (
            f"Duration: {format_time(analysis.track.duration_seconds)} | "
            f"Sample rate: {analysis.track.sample_rate} Hz | "
            f"Estimated BPM: {analysis.global_.bpm:.1f} | "
            f"Sections: {', '.join(section.label for section in analysis.sections) or 'none'}"
        )
    )


if __name__ == "__main__":
    app()
