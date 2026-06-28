import numpy as np

from groove_analyser.bands import compute_band_curves


def test_band_curves_are_normalized_without_nan():
    sr = 22050
    seconds = 2
    t = np.linspace(0, seconds, sr * seconds, endpoint=False)
    y = 0.5 * np.sin(2 * np.pi * 100 * t) + 0.2 * np.sin(2 * np.pi * 3000 * t)

    result = compute_band_curves(y, sr, hop_length=512)

    for curve in [*result.bands.values(), result.low, result.mid, result.high]:
        assert np.all(np.isfinite(curve))
        assert np.min(curve) >= 0.0
        assert np.max(curve) <= 1.0

    dumped = result.analysis.model_dump()
    assert dumped["summary"]["low_mean"] >= 0.0
