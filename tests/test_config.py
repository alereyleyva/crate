from groove_analyser.config import AnalysisConfig


def test_analysis_config_computes_hop_length_from_frame_rate():
    config = AnalysisConfig(frames_per_second=20)

    assert config.hop_length(44100) == 2205


def test_analysis_config_enforces_minimum_hop_length():
    config = AnalysisConfig(frames_per_second=1000)

    assert config.hop_length(44100) == 128
