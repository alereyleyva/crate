from groove_analyser.output import write_batch_index, write_track_outputs
from groove_analyser.schema import TrackAnalysis, TrackMetadata


def test_write_track_outputs_respects_requested_formats(tmp_path):
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

    written = write_track_outputs(analysis, tmp_path, export_json=True, export_markdown=False)

    assert set(written) == {"json"}
    assert (tmp_path / "track.analysis.json").exists()
    assert not (tmp_path / "track.report.md").exists()


def test_write_batch_index(tmp_path):
    index_path = write_batch_index(tmp_path, [{"filename": "track.wav", "json": "track.analysis.json"}])

    assert index_path.exists()
    assert '"tracks"' in index_path.read_text(encoding="utf-8")
