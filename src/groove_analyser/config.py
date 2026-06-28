from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisConfig:
    frames_per_second: int = 20
    target_sample_rate: int | None = 44100
    phrase_bars: int = 16

    def hop_length(self, sample_rate: int) -> int:
        return max(128, int(sample_rate / max(self.frames_per_second, 1)))
