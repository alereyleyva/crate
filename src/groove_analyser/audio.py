from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf


@dataclass(frozen=True)
class AudioData:
    path: Path
    y: np.ndarray
    sr: int
    channels: int
    duration: float


def load_audio(path: Path, target_sr: int | None = 44100) -> AudioData:
    info = sf.info(str(path))
    channels = max(1, int(info.channels or 1))
    y, sr = librosa.load(str(path), sr=target_sr, mono=True)
    y = np.nan_to_num(y.astype(float), nan=0.0, posinf=0.0, neginf=0.0)
    duration = float(librosa.get_duration(y=y, sr=sr))
    return AudioData(path=path, y=y, sr=int(sr), channels=channels, duration=duration)
