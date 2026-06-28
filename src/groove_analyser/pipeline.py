from __future__ import annotations

from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

from groove_analyser.audio import load_audio
from groove_analyser.bands import compute_band_curves, compute_spectral_data
from groove_analyser.beats import estimate_beat_grid
from groove_analyser.config import AnalysisConfig
from groove_analyser.features import compute_bar_features, compute_feature_curves, compute_global_features, compute_onset_envelope
from groove_analyser.mixpoints import build_llm_summary, detect_mix_points
from groove_analyser.schema import Timeline, TrackAnalysis, TrackMetadata
from groove_analyser.sections import detect_sections
from groove_analyser.utils import clamp01, safe_mean


def analyze_track(path: Path, config: AnalysisConfig | None = None) -> TrackAnalysis:
    config = config or AnalysisConfig()
    audio = load_audio(path, target_sr=config.target_sample_rate)
    hop_length = config.hop_length(audio.sr)
    spectral = compute_spectral_data(audio.y, audio.sr, hop_length, n_fft=config.n_fft)
    bands = compute_band_curves(audio.y, audio.sr, hop_length, n_fft=config.n_fft, spectral=spectral)
    onset_envelope = compute_onset_envelope(audio.y, audio.sr, hop_length, spectral=spectral)
    beat_grid = estimate_beat_grid(audio.y, audio.sr, audio.duration, hop_length, onset_envelope=onset_envelope)
    curves = compute_feature_curves(
        audio.y,
        audio.sr,
        hop_length,
        bands,
        spectral=spectral,
        onset_envelope=onset_envelope,
        key_mode=config.key_mode,
    )
    global_features = compute_global_features(curves, bands, beat_grid.bpm, beat_grid.tempo_confidence)
    bars = compute_bar_features(beat_grid.bar_times, curves, bands)
    if bars:
        bar_energies = sorted(bar.energy for bar in bars)
        upper_half = bar_energies[len(bar_energies) // 2 :]
        p75 = bar_energies[int(len(bar_energies) * 0.75)]
        global_features = global_features.model_copy(
            update={"energy": clamp01((safe_mean(upper_half) * 0.6) + (p75 * 0.4))}
        )
    sections = detect_sections(bars, phrase_bars=config.phrase_bars)
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
    return TrackAnalysis.model_validate(
        {
            "track": metadata,
            "global": global_features,
            "bands": bands.analysis,
            "timeline": Timeline(beats=beat_grid.beats, bars=bars),
            "sections": sections,
            "mix_points": mix_points,
            "llm": llm_summary,
        }
    )
