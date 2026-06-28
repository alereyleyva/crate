from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Annotated, NotRequired, TypedDict, cast

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from groove_analyser.config import AnalysisConfig, KeyMode
from groove_analyser.output import existing_track_outputs, write_batch_index, write_track_outputs
from groove_analyser.pipeline import analyze_track
from groove_analyser.utils import audio_files_in, format_time


app = typer.Typer(help="Groove Analyser: LLM-friendly music analysis for DJ-oriented tracks.")
console = Console()


class AnalysisResult(TypedDict):
    filename: str
    skipped: bool
    json: NotRequired[str]
    markdown: NotRequired[str]
    duration_seconds: NotRequired[float]
    sample_rate: NotRequired[int]
    bpm: NotRequired[float]
    sections: NotRequired[str]


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
    sample_rate: Annotated[int, typer.Option("--sample-rate", min=0, help="Target sample rate. Use 0 to keep the source rate.")] = 44100,
    n_fft: Annotated[int, typer.Option("--n-fft", min=512, max=8192, help="FFT window size used for spectral analysis.")] = 4096,
    key_mode: Annotated[str, typer.Option("--key-mode", help="Key estimation mode: stft, cqt or none.")] = "stft",
    fast: Annotated[bool, typer.Option("--fast/--quality", help="Use faster defaults: 22050 Hz, 10 fps, 2048 FFT and STFT key estimation.")] = False,
    workers: Annotated[int, typer.Option("--workers", "-w", min=0, help="Parallel workers for folder analysis. Use 0 for auto.")] = 0,
    skip_existing: Annotated[bool, typer.Option("--skip-existing/--force", help="Skip tracks whose requested outputs already exist.")] = False,
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
    config = _build_config(frames_per_second, sample_rate, n_fft, key_mode, fast)
    worker_count = _resolve_worker_count(workers, len(files))
    results_by_file: dict[Path, AnalysisResult] = {}

    if worker_count > 1:
        console.print(f"Using {worker_count} workers for {len(files)} tracks.")

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task(f"Analyzing 0/{len(files)} tracks", total=None)
        if worker_count == 1:
            for completed, file in enumerate(files, start=1):
                result = _analyze_file(file, track_out, export_json, export_markdown, config, skip_existing)
                results_by_file[file] = result
                _print_result_summary(result)
                progress.update(task, description=f"Analyzing {completed}/{len(files)} tracks")
        else:
            with ProcessPoolExecutor(max_workers=worker_count) as executor:
                futures = {
                    executor.submit(_analyze_file, file, track_out, export_json, export_markdown, config, skip_existing): file
                    for file in files
                }
                for completed, future in enumerate(as_completed(futures), start=1):
                    file = futures[future]
                    try:
                        result = future.result()
                    except Exception as exc:
                        console.print(f"[red]Failed to analyze {file}: {exc}[/red]")
                        raise typer.Exit(code=1) from exc
                    results_by_file[file] = result
                    _print_result_summary(result)
                    progress.update(task, description=f"Analyzing {completed}/{len(files)} tracks")

    index_entries = [_index_entry(results_by_file[file]) for file in files]

    if batch_mode:
        index_path = write_batch_index(out, index_entries)
        console.print(f"Wrote index: [green]{index_path}[/green]")

    for entry in index_entries:
        console.print(f"Analyzed [bold]{entry['filename']}[/bold]")
        if "json" in entry:
            console.print(f"JSON: [green]{entry['json']}[/green]")
        if "markdown" in entry:
            console.print(f"Markdown: [green]{entry['markdown']}[/green]")


def _build_config(frames_per_second: int, sample_rate: int, n_fft: int, key_mode: str, fast: bool) -> AnalysisConfig:
    normalized_key_mode = key_mode.lower()
    if normalized_key_mode not in {"stft", "cqt", "none"}:
        raise typer.BadParameter("--key-mode must be one of: stft, cqt, none")

    target_sample_rate: int | None = None if sample_rate == 0 else sample_rate
    resolved_frames_per_second = frames_per_second
    resolved_n_fft = n_fft
    if fast:
        target_sample_rate = 22050 if target_sample_rate is None else min(target_sample_rate, 22050)
        resolved_frames_per_second = min(resolved_frames_per_second, 10)
        resolved_n_fft = min(resolved_n_fft, 2048)
        if normalized_key_mode == "cqt":
            normalized_key_mode = "stft"

    return AnalysisConfig(
        frames_per_second=resolved_frames_per_second,
        target_sample_rate=target_sample_rate,
        n_fft=resolved_n_fft,
        key_mode=cast(KeyMode, normalized_key_mode),
    )


def _resolve_worker_count(requested_workers: int, file_count: int) -> int:
    if file_count <= 1:
        return 1
    if requested_workers > 0:
        return min(requested_workers, file_count)
    cpu_count = os.cpu_count() or 1
    auto_workers = max(1, cpu_count - 1)
    return min(file_count, auto_workers, 4)


def _analyze_file(
    file: Path,
    track_out: Path,
    export_json: bool,
    export_markdown: bool,
    config: AnalysisConfig,
    skip_existing: bool,
) -> AnalysisResult:
    if skip_existing:
        existing = existing_track_outputs(file.name, track_out, export_json, export_markdown)
        if existing is not None:
            return _result_with_outputs(file.name, existing, skipped=True)

    analysis = analyze_track(file, config=config)
    written = write_track_outputs(analysis, track_out, export_json, export_markdown)
    result = _result_with_outputs(file.name, written, skipped=False)
    result["duration_seconds"] = analysis.track.duration_seconds
    result["sample_rate"] = analysis.track.sample_rate
    result["bpm"] = analysis.global_.bpm
    result["sections"] = ", ".join(section.label for section in analysis.sections) or "none"
    return result


def _result_with_outputs(filename: str, outputs: dict[str, str], skipped: bool) -> AnalysisResult:
    result: AnalysisResult = {"filename": filename, "skipped": skipped}
    if "json" in outputs:
        result["json"] = outputs["json"]
    if "markdown" in outputs:
        result["markdown"] = outputs["markdown"]
    return result


def _index_entry(result: AnalysisResult) -> dict[str, str]:
    entry = {"filename": result["filename"]}
    if "json" in result:
        entry["json"] = result["json"]
    if "markdown" in result:
        entry["markdown"] = result["markdown"]
    return entry


def _print_result_summary(result: AnalysisResult) -> None:
    if result["skipped"]:
        console.print(f"Skipped existing [bold]{result['filename']}[/bold]")
        return
    console.print(
        (
            f"Duration: {format_time(result.get('duration_seconds', 0.0))} | "
            f"Sample rate: {result.get('sample_rate', 0)} Hz | "
            f"Estimated BPM: {result.get('bpm', 0.0):.1f} | "
            f"Sections: {result.get('sections', 'none')}"
        )
    )

if __name__ == "__main__":
    app()
