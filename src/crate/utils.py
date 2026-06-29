from __future__ import annotations

import math
from collections.abc import Iterable
from pathlib import Path
from typing import Any, cast

import numpy as np


AUDIO_EXTENSIONS = {".aif", ".aiff", ".flac", ".m4a", ".mp3", ".ogg", ".wav"}


def clamp01(value: object) -> float:
    numeric = safe_float(value)
    if not math.isfinite(numeric):
        return 0.0
    return max(0.0, min(1.0, numeric))


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        result = float(cast(Any, value))
    except (TypeError, ValueError):
        return default
    if not math.isfinite(result):
        return default
    return result


def safe_mean(values: np.ndarray | list[float]) -> float:
    array = np.asarray(values, dtype=float)
    if array.size == 0:
        return 0.0
    return safe_float(np.nanmean(array))


def safe_peak(values: np.ndarray | list[float]) -> float:
    array = np.asarray(values, dtype=float)
    if array.size == 0:
        return 0.0
    return safe_float(np.nanmax(array))


def normalize_curve(values: np.ndarray) -> np.ndarray:
    array = np.nan_to_num(np.asarray(values, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
    if array.size == 0:
        return array
    minimum = float(np.min(array))
    maximum = float(np.max(array))
    if maximum <= minimum:
        return np.zeros_like(array, dtype=float)
    return np.clip((array - minimum) / (maximum - minimum), 0.0, 1.0)


def mean_between(times: np.ndarray, values: np.ndarray, start: float, end: float) -> float:
    if values.size == 0 or times.size == 0:
        return 0.0
    mask = (times >= start) & (times < end)
    if not np.any(mask):
        nearest = int(np.argmin(np.abs(times - start)))
        return safe_float(values[nearest])
    return safe_mean(values[mask])


def vector_mean_between(times: np.ndarray, values: np.ndarray, start: float, end: float) -> list[float]:
    if values.size == 0 or times.size == 0:
        return [0.0] * 12
    mask = (times >= start) & (times < end)
    if not np.any(mask):
        nearest = int(np.argmin(np.abs(times - start)))
        vector = values[:, nearest]
    else:
        vector = np.nanmean(values[:, mask], axis=1)
    vector = np.nan_to_num(vector, nan=0.0, posinf=0.0, neginf=0.0)
    total = float(np.sum(vector))
    if total > 0:
        vector = vector / total
    return [clamp01(float(item)) for item in vector.tolist()]


def format_time(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    minutes, remainder = divmod(seconds, 60)
    return f"{minutes}:{remainder:02d}"


def audio_files_in(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix.lower() in AUDIO_EXTENSIONS else []
    files: Iterable[Path] = path.rglob("*") if path.is_dir() else []
    return sorted(file for file in files if file.is_file() and file.suffix.lower() in AUDIO_EXTENSIONS)
