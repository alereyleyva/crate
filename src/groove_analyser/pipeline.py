from __future__ import annotations

from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

from groove_analyser.audio import load_audio
from groove_analyser.bands import compute_band_curves
from groove_analyser.beats import estimate_beat_grid
from groove_analyser.features import compute_bar_features, compute_feature_curves, compute_global_features
from groove_analyser.mixpoints import build_llm_summary, detect_mix_points
from groove_analyser.schema import Timeline, TrackAnalysis, TrackMetadata
from groove_analyser.sections import detect_sections
from groove_analyser.utils import clamp01, safe_mean


def analyze_track(path: Path, frames_per_second: int = 20) -> TrackAnalysis:
    audio = load_audio(path)
    hop_length = max(128, int(audio.sr / max(frames_per_second, 1)))
    bands = compute_band_curves(audio.y, audio.sr, hop_length)
    beat_grid = estimate_beat_grid(audio.y, audio.sr, audio.duration, hop_length)
    curves = compute_feature_curves(audio.y, audio.sr, hop_length, bands)
    global_features = compute_global_features(curves, bands, beat_grid.bpm, beat_grid.tempo_confidence)
    bars = compute_bar_features(beat_grid.bar_times, curves, bands)
    if bars:
        bar_energies = sorted(bar.energy for bar in bars)
        upper_half = bar_energies[len(bar_energies) // 2 :]
        p75 = bar_energies[int(len(bar_energies) * 0.75)]
        global_features = global_features.model_copy(
            update={"energy": clamp01((safe_mean(upper_half) * 0.6) + (p75 * 0.4))}
        )
    sections = detect_sections(bars)
    mix_points = detect_mix_points(sections)
    llm_summary = build_llm_summary(global_features, sections, mix_points)
    metadata = TrackMetadata(
        id=str(uuid5(NAMESPACE_URL, str(path.resolve()))),
        filename=path.name,
        path=str(path),
        duration_seconds=audio.duration,
        sample_rate=audio.sr,
        channels=audio.channels,
    )
    return TrackAnalysis(
        track=metadata,
        global_=global_features,
        bands=bands.analysis,
        timeline=Timeline(beats=beat_grid.beats, bars=bars),
        sections=sections,
        mix_points=mix_points,
        llm=llm_summary,
    )
