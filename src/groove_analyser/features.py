from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import librosa

from groove_analyser.bands import BandCurves, SpectralData, compute_spectral_data
from groove_analyser.config import KeyMode
from groove_analyser.keys import estimate_key
from groove_analyser.schema import BarFeatures, GlobalFeatures
from groove_analyser.utils import clamp01, mean_between, normalize_curve, safe_mean, safe_peak, vector_mean_between


@dataclass(frozen=True)
class FeatureCurves:
    times: np.ndarray
    rms: np.ndarray
    centroid: np.ndarray
    bandwidth: np.ndarray
    rolloff: np.ndarray
    flatness: np.ndarray
    zcr: np.ndarray
    onset: np.ndarray
    flux: np.ndarray
    chroma: np.ndarray
    brightness: np.ndarray
    vocal_presence: np.ndarray


@dataclass(frozen=True)
class RawBarFeatures:
    start: float
    end: float
    raw_energy: float
    low: float
    mid: float
    high: float
    brightness: float
    onset_density: float
    vocal_presence_estimate: float
    chroma: list[float]


def compute_onset_envelope(
    y: np.ndarray,
    sr: int,
    hop_length: int,
    spectral: SpectralData | None = None,
) -> np.ndarray:
    if spectral is None:
        onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    else:
        spectrum_db = librosa.amplitude_to_db(spectral.magnitude, ref=np.max)
        onset = librosa.onset.onset_strength(S=spectrum_db, sr=sr, hop_length=hop_length)
    return np.nan_to_num(np.asarray(onset, dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)


def compute_feature_curves(
    y: np.ndarray,
    sr: int,
    hop_length: int,
    bands: BandCurves,
    spectral: SpectralData | None = None,
    onset_envelope: np.ndarray | None = None,
    key_mode: KeyMode = "stft",
) -> FeatureCurves:
    spectral = spectral or compute_spectral_data(y, sr, hop_length)
    magnitude = spectral.magnitude
    centroid_feature = librosa.feature.spectral_centroid(S=magnitude, sr=sr, freq=spectral.frequencies)
    rms_raw = librosa.feature.rms(S=magnitude, frame_length=spectral.n_fft, hop_length=hop_length)[0]
    centroid_raw = centroid_feature[0]
    bandwidth_raw = librosa.feature.spectral_bandwidth(S=magnitude, sr=sr, freq=spectral.frequencies, centroid=centroid_feature)[0]
    rolloff_raw = librosa.feature.spectral_rolloff(S=magnitude, sr=sr, freq=spectral.frequencies)[0]
    flatness_raw = librosa.feature.spectral_flatness(S=magnitude)[0]
    zcr_raw = librosa.feature.zero_crossing_rate(y, frame_length=spectral.n_fft, hop_length=hop_length)[0]
    onset_raw = onset_envelope if onset_envelope is not None else compute_onset_envelope(y, sr, hop_length, spectral)
    chroma = _compute_chroma(y, sr, hop_length, spectral, key_mode)

    min_frames = min(
        rms_raw.size,
        centroid_raw.size,
        bandwidth_raw.size,
        rolloff_raw.size,
        flatness_raw.size,
        zcr_raw.size,
        onset_raw.size,
        bands.low.size,
        chroma.shape[1],
    )
    rms = normalize_curve(rms_raw[:min_frames])
    centroid = np.clip(centroid_raw[:min_frames] / max(sr / 2.0, 1.0), 0.0, 1.0)
    bandwidth = np.clip(bandwidth_raw[:min_frames] / max(sr / 2.0, 1.0), 0.0, 1.0)
    rolloff = np.clip(rolloff_raw[:min_frames] / max(sr / 2.0, 1.0), 0.0, 1.0)
    flatness = np.clip(flatness_raw[:min_frames], 0.0, 1.0)
    zcr = normalize_curve(zcr_raw[:min_frames])
    onset = normalize_curve(onset_raw[:min_frames])
    flux = normalize_curve(np.abs(np.diff(rms, prepend=rms[0] if rms.size else 0.0)))
    high = bands.high[:min_frames]
    mid = bands.mid[:min_frames]
    low = bands.low[:min_frames]
    brightness = np.clip((centroid * 0.5) + (high * 0.5), 0.0, 1.0)
    vocal_presence = np.clip(
        (mid * 0.45) + ((1.0 - onset) * 0.25) + ((1.0 - low) * 0.15) + ((1.0 - flatness) * 0.15),
        0.0,
        1.0,
    )
    times = bands.times[:min_frames]
    return FeatureCurves(
        times=times,
        rms=rms,
        centroid=centroid,
        bandwidth=bandwidth,
        rolloff=rolloff,
        flatness=flatness,
        zcr=zcr,
        onset=onset,
        flux=flux,
        chroma=chroma[:, :min_frames],
        brightness=brightness,
        vocal_presence=vocal_presence,
    )


def _compute_chroma(
    y: np.ndarray,
    sr: int,
    hop_length: int,
    spectral: SpectralData,
    key_mode: KeyMode,
) -> np.ndarray:
    if key_mode == "none":
        return np.zeros((12, spectral.power.shape[1]), dtype=np.float32)
    if key_mode == "cqt":
        try:
            return librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)
        except Exception:
            pass
    return librosa.feature.chroma_stft(S=spectral.power, sr=sr, n_fft=spectral.n_fft)


def compute_global_features(curves: FeatureCurves, bands: BandCurves, bpm: float, tempo_confidence: float) -> GlobalFeatures:
    key, key_confidence, camelot = estimate_key(curves.chroma)
    energy = clamp01((safe_mean(curves.rms) * 0.5) + (safe_mean(curves.onset) * 0.25) + (safe_mean((bands.low[: curves.rms.size] + bands.mid[: curves.rms.size] + bands.high[: curves.rms.size]) / 3.0) * 0.25))
    bass_weight = clamp01(safe_mean(bands.low[: curves.rms.size]))
    brightness = clamp01(safe_mean(curves.brightness))
    percussiveness = clamp01((safe_mean(curves.onset) * 0.7) + (safe_mean(curves.flux) * 0.3))
    dynamic_range = clamp01(safe_peak(curves.rms) - safe_mean(curves.rms))
    return GlobalFeatures(
        bpm=bpm,
        tempo_confidence=tempo_confidence,
        key=key,
        key_confidence=key_confidence,
        camelot=camelot,
        energy=energy,
        bass_weight=bass_weight,
        brightness=brightness,
        percussiveness=percussiveness,
        dynamic_range=dynamic_range,
        vocal_presence_estimate=clamp01(safe_mean(curves.vocal_presence)),
        spectral_centroid=clamp01(safe_mean(curves.centroid)),
        spectral_bandwidth=clamp01(safe_mean(curves.bandwidth)),
        spectral_rolloff=clamp01(safe_mean(curves.rolloff)),
        spectral_flatness=clamp01(safe_mean(curves.flatness)),
        rms_energy=clamp01(safe_mean(curves.rms)),
        zero_crossing_rate=clamp01(safe_mean(curves.zcr)),
    )


def compute_bar_features(bar_times: list[tuple[float, float]], curves: FeatureCurves, bands: BandCurves) -> list[BarFeatures]:
    raw_bars: list[RawBarFeatures] = []
    raw_energies: list[float] = []
    for start, end in bar_times:
        low = mean_between(bands.times, bands.low, start, end)
        mid = mean_between(bands.times, bands.mid, start, end)
        high = mean_between(bands.times, bands.high, start, end)
        raw_energy = clamp01((mean_between(curves.times, curves.rms, start, end) * 0.55) + (mean_between(curves.times, curves.onset, start, end) * 0.25) + (((low + mid + high) / 3.0) * 0.2))
        raw_energies.append(raw_energy)
        raw_bars.append(
            RawBarFeatures(
                start=float(start),
                end=float(end),
                raw_energy=raw_energy,
                low=low,
                mid=mid,
                high=high,
                brightness=clamp01((mean_between(curves.times, curves.centroid, start, end) * 0.5) + (high * 0.5)),
                onset_density=mean_between(curves.times, curves.onset, start, end),
                vocal_presence_estimate=mean_between(curves.times, curves.vocal_presence, start, end),
                chroma=vector_mean_between(curves.times, curves.chroma, start, end),
            )
        )

    relative_energies = normalize_curve(np.asarray(raw_energies, dtype=float))
    bars: list[BarFeatures] = []
    for index, raw_bar in enumerate(raw_bars, start=1):
        bars.append(
            BarFeatures(
                index=index,
                start=raw_bar.start,
                end=raw_bar.end,
                energy=float(relative_energies[index - 1]) if relative_energies.size else 0.0,
                low=raw_bar.low,
                mid=raw_bar.mid,
                high=raw_bar.high,
                bass_weight=raw_bar.low,
                brightness=raw_bar.brightness,
                onset_density=raw_bar.onset_density,
                vocal_presence_estimate=raw_bar.vocal_presence_estimate,
                chroma=raw_bar.chroma,
            )
        )
    return bars
