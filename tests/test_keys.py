import numpy as np

from groove_analyser.keys import estimate_key


def test_estimate_key_handles_empty_chroma():
    assert estimate_key(np.asarray([])) == ("Unknown", 0.0, "Unknown")


def test_estimate_key_returns_key_confidence_and_camelot():
    chroma = np.zeros((12, 8))
    chroma[0, :] = 1.0

    key, confidence, camelot = estimate_key(chroma)

    assert key != "Unknown"
    assert 0.0 <= confidence <= 1.0
    assert camelot != "Unknown"
