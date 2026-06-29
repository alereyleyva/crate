from __future__ import annotations

from crate.schema import BarFeatures, Section, SectionLabel
from crate.utils import clamp01, safe_mean, safe_peak


def _section_label(position: float, energy: float, bass: float, onset: float, total_groups: int) -> SectionLabel:
    if position < 0.18 and energy < 0.65:
        return "intro"
    if position > 0.82 and energy < 0.7:
        return "outro"
    if energy < 0.35 and onset < 0.35:
        return "breakdown"
    if energy > 0.75 or (energy > 0.65 and bass > 0.45):
        return "drop"
    if total_groups > 2 and 0.35 <= position <= 0.75 and onset > 0.5 and energy > 0.5:
        return "build"
    if energy >= 0.4:
        return "groove"
    return "unknown"


def _description(label: SectionLabel, energy: float, bass: float, vocal: float) -> str:
    density = "high-energy" if energy > 0.7 else "moderate" if energy > 0.4 else "reduced"
    low_end = "strong low-end" if bass > 0.65 else "controlled low-end"
    vocal_text = "noticeable vocal/midrange presence" if vocal > 0.55 else "low vocal presence"
    return f"{label.capitalize()} section with {density} arrangement, {low_end} and {vocal_text}."


def detect_sections(bars: list[BarFeatures], phrase_bars: int = 16) -> list[Section]:
    if not bars:
        return []
    groups = [bars[index : index + phrase_bars] for index in range(0, len(bars), phrase_bars)]
    sections: list[Section] = []
    total_groups = len(groups)

    for group_index, group in enumerate(groups):
        energies = [bar.energy for bar in group]
        bass_values = [bar.bass_weight for bar in group]
        brightness_values = [bar.brightness for bar in group]
        vocal_values = [bar.vocal_presence_estimate for bar in group]
        onset_values = [bar.onset_density for bar in group]
        energy_mean = safe_mean(energies)
        bass = safe_mean(bass_values)
        vocal = safe_mean(vocal_values)
        position = group_index / max(total_groups - 1, 1)
        label = _section_label(position, energy_mean, bass, safe_mean(onset_values), total_groups)
        moderate_energy = 1.0 - abs(energy_mean - 0.5) * 2.0
        mixability = clamp01(
            (0.25 * safe_mean(onset_values))
            + 0.20
            + (0.20 * (1.0 - vocal))
            + (0.15 * moderate_energy)
            + (0.10 * (1.0 - safe_mean(brightness_values)))
            + (0.10 * (1.0 - bass))
        )
        sections.append(
            Section(
                label=label,
                start=group[0].start,
                end=group[-1].end,
                start_bar=group[0].index,
                end_bar=group[-1].index,
                energy_mean=energy_mean,
                energy_peak=safe_peak(energies),
                bass_weight=bass,
                brightness=safe_mean(brightness_values),
                vocal_presence_estimate=vocal,
                mixability=mixability,
                description=_description(label, energy_mean, bass, vocal),
            )
        )

    return _merge_adjacent_sections(sections)


def _merge_adjacent_sections(sections: list[Section]) -> list[Section]:
    if not sections:
        return []
    merged: list[Section] = [sections[0]]
    for section in sections[1:]:
        previous = merged[-1]
        if section.label == previous.label:
            merged[-1] = Section(
                label=previous.label,
                start=previous.start,
                end=section.end,
                start_bar=previous.start_bar,
                end_bar=section.end_bar,
                energy_mean=safe_mean([previous.energy_mean, section.energy_mean]),
                energy_peak=max(previous.energy_peak, section.energy_peak),
                bass_weight=safe_mean([previous.bass_weight, section.bass_weight]),
                brightness=safe_mean([previous.brightness, section.brightness]),
                vocal_presence_estimate=safe_mean([previous.vocal_presence_estimate, section.vocal_presence_estimate]),
                mixability=safe_mean([previous.mixability, section.mixability]),
                description=previous.description,
            )
        else:
            merged.append(section)
    return merged
