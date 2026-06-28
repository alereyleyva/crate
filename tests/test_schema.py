from groove_analyser.schema import TrackAnalysis, TrackMetadata


def test_track_analysis_schema_serializes_with_global_alias():
    analysis = TrackAnalysis(
        track=TrackMetadata(
            id="abc",
            filename="track.wav",
            path="track.wav",
            duration_seconds=10.0,
            sample_rate=44100,
            channels=2,
        )
    )

    data = analysis.model_dump(by_alias=True)
    assert data["version"] == "0.1.0"
    assert "global" in data
    assert "global_" not in data


def test_normalized_schema_values_are_clamped():
    analysis = TrackAnalysis.model_validate(
        {
            "track": {
                "id": "abc",
                "filename": "track.wav",
                "path": "track.wav",
                "duration_seconds": 10.0,
                "sample_rate": 44100,
                "channels": 2,
            },
            "global": {"energy": 2.0, "bass_weight": -1.0},
        }
    )

    assert analysis.global_.energy == 1.0
    assert analysis.global_.bass_weight == 0.0
