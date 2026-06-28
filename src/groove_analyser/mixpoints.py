from __future__ import annotations

from groove_analyser.schema import GlobalFeatures, LLMSummary, MixPoints, MixRegion, RiskRegion, Section
from groove_analyser.utils import clamp01


def detect_mix_points(sections: list[Section]) -> MixPoints:
    if not sections:
        return MixPoints()

    candidates = sorted(sections, key=lambda section: section.mixability, reverse=True)
    intro_candidates = sorted(sections[: max(1, min(3, len(sections)))], key=lambda section: section.mixability, reverse=True)
    outro_candidates = _mix_out_candidates(sections)

    best_mix_in = [_mix_region(section, "Stable phrase-aligned section with relatively low vocal presence.") for section in intro_candidates[:2]]
    best_mix_out = [_mix_region(section, "Reduced or phrase-aligned section suitable for transitioning out.") for section in outro_candidates[:2]]
    safe_loop_regions = [_mix_region(section, "Loopable phrase with balanced energy and manageable spectral density.") for section in candidates if section.mixability >= 0.62][:3]
    high_risk_regions = [_risk_region(section) for section in sections if _is_high_risk(section)]

    return MixPoints(
        best_mix_in=best_mix_in,
        best_mix_out=best_mix_out,
        safe_loop_regions=safe_loop_regions,
        high_risk_regions=high_risk_regions,
    )


def _mix_out_candidates(sections: list[Section]) -> list[Section]:
    late_sections = list(reversed(sections[-max(1, min(5, len(sections))) :]))
    preferred = [
        section
        for section in late_sections
        if section.label in {"outro", "groove", "intro", "unknown"} and section.energy_mean < 0.75
    ]
    if preferred:
        return preferred[:2]
    return late_sections[:2]


def _mix_region(section: Section, reason: str) -> MixRegion:
    return MixRegion(
        start=section.start,
        end=section.end,
        start_bar=section.start_bar,
        end_bar=section.end_bar,
        score=clamp01(section.mixability),
        reason=reason,
    )


def _is_high_risk(section: Section) -> bool:
    return (
        section.label == "drop"
        or (section.energy_peak > 0.9 and section.energy_mean > 0.7)
        or section.vocal_presence_estimate > 0.65
        or (section.label == "breakdown" and section.mixability < 0.45)
        or (section.bass_weight > 0.72 and section.energy_mean > 0.62)
    )


def _risk_region(section: Section) -> RiskRegion:
    if section.label == "drop" or section.energy_peak > 0.82:
        reason = "Dense high-energy section; avoid overlapping with another drop."
    elif section.vocal_presence_estimate > 0.65:
        reason = "Noticeable vocal/midrange presence may clash with another lead element."
    elif section.label == "breakdown":
        reason = "Low rhythmic density can make direct beatmatching less reliable."
    else:
        reason = "Strong low-end may create bass clashes."
    return RiskRegion(start=section.start, end=section.end, start_bar=section.start_bar, end_bar=section.end_bar, reason=reason)


def build_llm_summary(global_features: GlobalFeatures, sections: list[Section], mix_points: MixPoints) -> LLMSummary:
    energy_word = "high-energy" if global_features.energy > 0.68 else "moderate-energy" if global_features.energy > 0.38 else "low-energy"
    bass_word = "bass-heavy" if global_features.bass_weight > 0.62 else "balanced low-end"
    vocal_word = "sparse vocals" if global_features.vocal_presence_estimate < 0.55 else "noticeable vocal or midrange content"
    section_labels = [section.label for section in sections]
    unique_sections = list(dict.fromkeys(section_labels))
    summary = (
        f"{energy_word.capitalize()} electronic track at {global_features.bpm:.1f} BPM in {global_features.key} "
        f"({global_features.camelot}), with {bass_word} and {vocal_word}. "
        f"Detected structure: {', '.join(unique_sections) if unique_sections else 'unknown'}."
    )
    strategy = (
        f"Match with tracks around {max(0, global_features.bpm - 2):.0f}-{global_features.bpm + 2:.0f} BPM, "
        f"compatible Camelot keys near {global_features.camelot}, and avoid layering bass-heavy or vocal-heavy sections."
    )
    warnings = [region.reason for region in mix_points.high_risk_regions[:3]]
    if not warnings and global_features.bass_weight > 0.6:
        warnings.append("Track has strong low-end; monitor bass clashes during transitions.")
    tags = ["electronic", energy_word, bass_word]
    if global_features.vocal_presence_estimate < 0.55:
        tags.append("instrumental")
    if any(section.label == "drop" for section in sections):
        tags.append("drop-focused")
    return LLMSummary(summary=summary, recommended_matching_strategy=strategy, warnings=warnings, tags=tags)
