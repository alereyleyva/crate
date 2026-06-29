from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


KeyMode = Literal["stft", "cqt", "none"]


@dataclass(frozen=True)
class AnalysisConfig:
    frames_per_second: int = 20
    target_sample_rate: int | None = 44100
    phrase_bars: int = 16
    n_fft: int = 4096
    key_mode: KeyMode = "stft"

    def hop_length(self, sample_rate: int) -> int:
        return max(128, int(sample_rate / max(self.frames_per_second, 1)))
