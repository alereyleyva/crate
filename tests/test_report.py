from crate.report import render_markdown
from crate.schema import LLMSummary, Section, TrackAnalysis, TrackMetadata


def test_report_contains_expected_sections():
    analysis = TrackAnalysis(
        track=TrackMetadata(
            id="abc",
            filename="track.wav",
            path="track.wav",
            duration_seconds=120.0,
            sample_rate=44100,
            channels=2,
        ),
        sections=[
            Section(
                label="intro",
                start=0.0,
                end=32.0,
                start_bar=1,
                end_bar=16,
                energy_mean=0.4,
                energy_peak=0.5,
                bass_weight=0.3,
                brightness=0.2,
                vocal_presence_estimate=0.1,
                mixability=0.8,
                description="Clean intro.",
            )
        ],
        llm=LLMSummary(summary="A concise LLM summary.", recommended_matching_strategy="Match by BPM and key."),
    )

    markdown = render_markdown(analysis)

    assert "# Track Analysis Report" in markdown
    assert "## Structure" in markdown
    assert "## LLM Summary" in markdown
    assert "A concise LLM summary." in markdown
