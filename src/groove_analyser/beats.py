from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import librosa

from groove_analyser.schema import Beat
from groove_analyser.utils import clamp01, safe_float


@dataclass(frozen=True)
class BeatGrid:
    bpm: float
    tempo_confidence: float
    beat_times: np.ndarray
    bar_times: list[tuple[float, float]]
    beats: list[Beat]


def estimate_beat_grid(y: np.ndarray, sr: int, duration: float, hop_length: int) -> BeatGrid:
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, onset_envelope=onset_env, hop_length=hop_length, trim=False)
    tempo_value = safe_float(np.asarray(tempo).reshape(-1)[0] if np.asarray(tempo).size else tempo)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length)
    fallback_used = False

    if tempo_value <= 0:
        tempo_value = 120.0
    if beat_times.size < 4:
        fallback_used = True
        interval = 60.0 / tempo_value
        beat_times = np.arange(0.0, max(duration, interval), interval)

    tempo_value, beat_times = _normalize_dj_tempo(tempo_value, beat_times, duration)

    beat_intervals = np.diff(beat_times)
    if beat_intervals.size > 1:
        stability = 1.0 - (float(np.std(beat_intervals)) / max(float(np.mean(beat_intervals)), 1e-6))
    else:
        stability = 0.0
    tempo_confidence = clamp01(stability)
    if fallback_used:
        tempo_confidence = min(tempo_confidence, 0.25)

    bar_times: list[tuple[float, float]] = []
    for start_index in range(0, max(0, beat_times.size - 3), 4):
        start = float(beat_times[start_index])
        if start_index + 4 < beat_times.size:
            end = float(beat_times[start_index + 4])
        else:
            end = min(duration, start + (60.0 / tempo_value) * 4.0)
        if end > start:
            bar_times.append((start, min(float(duration), end)))

    if not bar_times:
        bar_length = (60.0 / tempo_value) * 4.0
        starts = np.arange(0.0, duration, bar_length)
        bar_times = [(float(start), float(min(duration, start + bar_length))) for start in starts]

    beats = [Beat(index=index + 1, time=float(time)) for index, time in enumerate(beat_times.tolist())]
    return BeatGrid(bpm=round(float(tempo_value), 2), tempo_confidence=tempo_confidence, beat_times=beat_times, bar_times=bar_times, beats=beats)


def _normalize_dj_tempo(tempo: float, beat_times: np.ndarray, duration: float) -> tuple[float, np.ndarray]:
    if 60.0 <= tempo < 90.0 and beat_times.size >= 2:
        return tempo * 2.0, _insert_half_beats(beat_times, duration)
    if tempo > 180.0 and beat_times.size >= 2:
        return tempo / 2.0, beat_times[::2]
    return tempo, beat_times


def _insert_half_beats(beat_times: np.ndarray, duration: float) -> np.ndarray:
    doubled: list[float] = []
    for index, start in enumerate(beat_times):
        doubled.append(float(start))
        if index + 1 < beat_times.size:
            end = float(beat_times[index + 1])
            doubled.append(start + ((end - start) / 2.0))
    if len(doubled) >= 2:
        interval = doubled[-1] - doubled[-2]
        next_time = doubled[-1] + interval
        while next_time < duration:
            doubled.append(float(next_time))
            next_time += interval
    return np.asarray(sorted(time for time in doubled if time <= duration), dtype=float)
