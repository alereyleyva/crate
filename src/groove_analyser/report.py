from __future__ import annotations

from groove_analyser.schema import TrackAnalysis
from groove_analyser.utils import format_time


def render_markdown(analysis: TrackAnalysis) -> str:
    global_features = analysis.global_
    lines = [
        "# Track Analysis Report",
        "",
        "## Track",
        "",
        f"- File: {analysis.track.filename}",
        f"- Duration: {format_time(analysis.track.duration_seconds)}",
        f"- BPM: {global_features.bpm:.1f}",
        f"- Key: {global_features.key}",
        f"- Camelot: {global_features.camelot}",
        f"- Energy: {global_features.energy:.2f}",
        f"- Bass weight: {global_features.bass_weight:.2f}",
        f"- Brightness: {global_features.brightness:.2f}",
        f"- Vocal presence: {global_features.vocal_presence_estimate:.2f}",
        "",
        "## High-level Summary",
        "",
        analysis.llm.summary or "No summary available.",
        "",
        "## Structure",
        "",
        "| Section | Start | End | Bars | Energy | Mixability | Notes |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for section in analysis.sections:
        lines.append(
            f"| {section.label.capitalize()} | {format_time(section.start)} | {format_time(section.end)} | "
            f"{section.start_bar}-{section.end_bar} | {section.energy_mean:.2f} | {section.mixability:.2f} | {section.description} |"
        )

    lines.extend([
        "",
        "## Mix-in Recommendations",
        "",
    ])
    lines.extend(_render_mix_regions(analysis.mix_points.best_mix_in))
    lines.extend([
        "",
        "## Mix-out Recommendations",
        "",
    ])
    lines.extend(_render_mix_regions(analysis.mix_points.best_mix_out))
    lines.extend([
        "",
        "## Matching Notes",
        "",
        analysis.llm.recommended_matching_strategy or "No matching strategy available.",
        "",
        "## Risks",
        "",
    ])
    if analysis.mix_points.high_risk_regions:
        for region in analysis.mix_points.high_risk_regions:
            lines.append(f"- {format_time(region.start)}-{format_time(region.end)}: {region.reason}")
    elif analysis.llm.warnings:
        lines.extend(f"- {warning}" for warning in analysis.llm.warnings)
    else:
        lines.append("- No major high-risk regions detected by the v1 heuristics.")

    lines.extend([
        "",
        "## LLM Summary",
        "",
        analysis.llm.summary,
    ])
    return "\n".join(lines).strip() + "\n"


def _render_mix_regions(regions) -> list[str]:
    if not regions:
        return ["No strong candidates detected by the v1 heuristics."]
    return [
        f"- {format_time(region.start)}-{format_time(region.end)} "
        f"(bars {region.start_bar}-{region.end_bar}, score {region.score:.2f}): {region.reason}"
        for region in regions
    ]
