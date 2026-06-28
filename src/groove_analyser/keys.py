from __future__ import annotations

import numpy as np

from groove_analyser.utils import clamp01


KEY_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
MAJOR_CAMELOT = {
    "C": "8B",
    "C#": "3B",
    "D": "10B",
    "D#": "5B",
    "E": "12B",
    "F": "7B",
    "F#": "2B",
    "G": "9B",
    "G#": "4B",
    "A": "11B",
    "A#": "6B",
    "B": "1B",
}
MINOR_CAMELOT = {
    "C": "5A",
    "C#": "12A",
    "D": "7A",
    "D#": "2A",
    "E": "9A",
    "F": "4A",
    "F#": "11A",
    "G": "6A",
    "G#": "1A",
    "A": "8A",
    "A#": "3A",
    "B": "10A",
}


def estimate_key(chroma: np.ndarray) -> tuple[str, float, str]:
    if chroma.size == 0:
        return "Unknown", 0.0, "Unknown"

    profile = np.nanmean(chroma, axis=1)
    if float(np.sum(profile)) <= 0:
        return "Unknown", 0.0, "Unknown"

    profile = profile / np.sum(profile)
    scores: list[tuple[float, str, str]] = []
    for index, name in enumerate(KEY_NAMES):
        major = np.roll(MAJOR_PROFILE, index)
        minor = np.roll(MINOR_PROFILE, index)
        scores.append((_safe_correlation(profile, major), f"{name} major", MAJOR_CAMELOT[name]))
        scores.append((_safe_correlation(profile, minor), f"{name} minor", MINOR_CAMELOT[name]))

    scores.sort(reverse=True, key=lambda item: item[0])
    best_score, key, camelot = scores[0]
    second_score = scores[1][0] if len(scores) > 1 else 0.0
    confidence = clamp01((best_score - second_score + 0.25) / 0.5)
    return key, confidence, camelot


def _safe_correlation(profile: np.ndarray, template: np.ndarray) -> float:
    score = float(np.corrcoef(profile, template)[0, 1])
    return score if np.isfinite(score) else 0.0
