from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from groove_analyser import __version__
from groove_analyser.utils import clamp01, safe_float


SectionLabel = Literal["intro", "groove", "breakdown", "build", "drop", "outro", "unknown"]


class GrooveBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class TrackMetadata(GrooveBaseModel):
    id: str
    filename: str
    path: str
    duration_seconds: float
    sample_rate: int
    channels: int


class GlobalFeatures(GrooveBaseModel):
    bpm: float = 0.0
    tempo_confidence: float = 0.0
    key: str = "Unknown"
    key_confidence: float = 0.0
    camelot: str = "Unknown"
    energy: float = 0.0
    bass_weight: float = 0.0
    brightness: float = 0.0
    percussiveness: float = 0.0
    dynamic_range: float = 0.0
    vocal_presence_estimate: float = 0.0
    spectral_centroid: float = 0.0
    spectral_bandwidth: float = 0.0
    spectral_rolloff: float = 0.0
    spectral_flatness: float = 0.0
    rms_energy: float = 0.0
    zero_crossing_rate: float = 0.0

    @field_validator(
        "tempo_confidence",
        "key_confidence",
        "energy",
        "bass_weight",
        "brightness",
        "percussiveness",
        "dynamic_range",
        "vocal_presence_estimate",
        "spectral_centroid",
        "spectral_bandwidth",
        "spectral_rolloff",
        "spectral_flatness",
        "rms_energy",
        "zero_crossing_rate",
    )
    @classmethod
    def normalized(cls, value: float) -> float:
        return clamp01(value)

    @field_validator("bpm")
    @classmethod
    def clean_bpm(cls, value: float) -> float:
        return max(0.0, safe_float(value))


class BandDefinitions(GrooveBaseModel):
    sub: tuple[int, int] = (20, 60)
    bass: tuple[int, int] = (60, 250)
    low_mid: tuple[int, int] = (250, 800)
    mid: tuple[int, int] = (800, 2500)
    high_mid: tuple[int, int] = (2500, 6000)
    high: tuple[int, int] = (6000, 16000)


class BandSummary(GrooveBaseModel):
    low_mean: float = 0.0
    mid_mean: float = 0.0
    high_mean: float = 0.0
    low_peak: float = 0.0
    mid_peak: float = 0.0
    high_peak: float = 0.0

    @field_validator("*")
    @classmethod
    def normalized(cls, value: float) -> float:
        return clamp01(value)


class BandAnalysis(GrooveBaseModel):
    definitions_hz: BandDefinitions = Field(default_factory=BandDefinitions)
    summary: BandSummary = Field(default_factory=BandSummary)


class Beat(GrooveBaseModel):
    index: int
    time: float


class BarFeatures(GrooveBaseModel):
    index: int
    start: float
    end: float
    energy: float = 0.0
    low: float = 0.0
    mid: float = 0.0
    high: float = 0.0
    bass_weight: float = 0.0
    brightness: float = 0.0
    onset_density: float = 0.0
    vocal_presence_estimate: float = 0.0
    chroma: list[float] = Field(default_factory=lambda: [0.0] * 12, min_length=12, max_length=12)

    @field_validator("energy", "low", "mid", "high", "bass_weight", "brightness", "onset_density", "vocal_presence_estimate")
    @classmethod
    def normalized(cls, value: float) -> float:
        return clamp01(value)

    @field_validator("chroma")
    @classmethod
    def normalized_chroma(cls, value: list[float]) -> list[float]:
        return [clamp01(item) for item in value]


class Timeline(GrooveBaseModel):
    beats: list[Beat] = Field(default_factory=list)
    bars: list[BarFeatures] = Field(default_factory=list)


class Section(GrooveBaseModel):
    label: SectionLabel
    start: float
    end: float
    start_bar: int
    end_bar: int
    energy_mean: float = 0.0
    energy_peak: float = 0.0
    bass_weight: float = 0.0
    brightness: float = 0.0
    vocal_presence_estimate: float = 0.0
    mixability: float = 0.0
    description: str = ""

    @field_validator("energy_mean", "energy_peak", "bass_weight", "brightness", "vocal_presence_estimate", "mixability")
    @classmethod
    def normalized(cls, value: float) -> float:
        return clamp01(value)


class MixRegion(GrooveBaseModel):
    start: float
    end: float
    start_bar: int | None = None
    end_bar: int | None = None
    score: float = 0.0
    reason: str

    @field_validator("score")
    @classmethod
    def normalized(cls, value: float) -> float:
        return clamp01(value)


class RiskRegion(GrooveBaseModel):
    start: float
    end: float
    start_bar: int | None = None
    end_bar: int | None = None
    reason: str


class MixPoints(GrooveBaseModel):
    best_mix_in: list[MixRegion] = Field(default_factory=list)
    best_mix_out: list[MixRegion] = Field(default_factory=list)
    safe_loop_regions: list[MixRegion] = Field(default_factory=list)
    high_risk_regions: list[RiskRegion] = Field(default_factory=list)


class LLMSummary(GrooveBaseModel):
    summary: str = ""
    recommended_matching_strategy: str = ""
    warnings: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class TrackAnalysis(GrooveBaseModel):
    version: str = __version__
    track: TrackMetadata
    global_: GlobalFeatures = Field(default_factory=GlobalFeatures, alias="global")
    bands: BandAnalysis = Field(default_factory=BandAnalysis)
    timeline: Timeline = Field(default_factory=Timeline)
    sections: list[Section] = Field(default_factory=list)
    mix_points: MixPoints = Field(default_factory=MixPoints)
    llm: LLMSummary = Field(default_factory=LLMSummary)
