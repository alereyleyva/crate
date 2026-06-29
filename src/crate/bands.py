from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import librosa

from crate.schema import BandAnalysis, BandDefinitions, BandSummary
from crate.utils import clamp01, normalize_curve, safe_mean, safe_peak


BAND_DEFINITIONS: dict[str, tuple[int, int]] = {
    "sub": (20, 60),
    "bass": (60, 250),
    "low_mid": (250, 800),
    "mid": (800, 2500),
    "high_mid": (2500, 6000),
    "high": (6000, 16000),
}


@dataclass(frozen=True)
class SpectralData:
    n_fft: int
    hop_length: int
    magnitude: np.ndarray
    power: np.ndarray
    frequencies: np.ndarray
    times: np.ndarray


@dataclass(frozen=True)
class BandCurves:
    times: np.ndarray
    bands: dict[str, np.ndarray]
    low: np.ndarray
    mid: np.ndarray
    high: np.ndarray
    analysis: BandAnalysis


def compute_spectral_data(y: np.ndarray, sr: int, hop_length: int, n_fft: int = 4096) -> SpectralData:
    stft = librosa.stft(y, n_fft=n_fft, hop_length=hop_length)
    magnitude = np.abs(stft).astype(np.float32, copy=False)
    power = np.square(magnitude).astype(np.float32, copy=False)
    frequencies = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    times = librosa.frames_to_time(np.arange(power.shape[1]), sr=sr, hop_length=hop_length)
    return SpectralData(
        n_fft=n_fft,
        hop_length=hop_length,
        magnitude=magnitude,
        power=power,
        frequencies=frequencies,
        times=times,
    )


def compute_band_curves(
    y: np.ndarray,
    sr: int,
    hop_length: int,
    n_fft: int = 4096,
    spectral: SpectralData | None = None,
) -> BandCurves:
    spectral = spectral or compute_spectral_data(y, sr, hop_length, n_fft=n_fft)
    power = spectral.power
    frequencies = spectral.frequencies
    times = spectral.times

    band_curves: dict[str, np.ndarray] = {}
    for name, (low_hz, high_hz) in BAND_DEFINITIONS.items():
        mask = (frequencies >= low_hz) & (frequencies < min(high_hz, sr / 2))
        if np.any(mask):
            curve = np.mean(power[mask, :], axis=0)
        else:
            curve = np.zeros(power.shape[1], dtype=float)
        band_curves[name] = normalize_curve(curve)

    low_curve = np.clip((band_curves["sub"] + band_curves["bass"]) / 2.0, 0.0, 1.0)
    mid_curve = np.clip((band_curves["low_mid"] + band_curves["mid"]) / 2.0, 0.0, 1.0)
    high_curve = np.clip((band_curves["high_mid"] + band_curves["high"]) / 2.0, 0.0, 1.0)

    summary = BandSummary(
        low_mean=clamp01(safe_mean(low_curve)),
        mid_mean=clamp01(safe_mean(mid_curve)),
        high_mean=clamp01(safe_mean(high_curve)),
        low_peak=clamp01(safe_peak(low_curve)),
        mid_peak=clamp01(safe_peak(mid_curve)),
        high_peak=clamp01(safe_peak(high_curve)),
    )
    analysis = BandAnalysis(definitions_hz=BandDefinitions(), summary=summary)
    return BandCurves(times=times, bands=band_curves, low=low_curve, mid=mid_curve, high=high_curve, analysis=analysis)
