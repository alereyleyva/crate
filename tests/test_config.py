from crate.config import AnalysisConfig


def test_analysis_config_computes_hop_length_from_frame_rate():
    config = AnalysisConfig(frames_per_second=20)

    assert config.hop_length(44100) == 2205


def test_analysis_config_enforces_minimum_hop_length():
    config = AnalysisConfig(frames_per_second=1000)

    assert config.hop_length(44100) == 128


def test_analysis_config_exposes_performance_knobs():
    config = AnalysisConfig(target_sample_rate=22050, n_fft=2048, key_mode="none")

    assert config.target_sample_rate == 22050
    assert config.n_fft == 2048
    assert config.key_mode == "none"
