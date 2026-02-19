import pytest
from app.services.clip_engine import ClipEngine


class TestClipEngine:
    def setup_method(self):
        self.engine = ClipEngine()

    def test_parse_srt_basic(self):
        srt = """1
00:00:01,000 --> 00:00:04,000
Hello, world!

2
00:00:05,000 --> 00:00:08,500
How are you?
"""
        entries = self.engine._parse_srt(srt)
        assert len(entries) == 2
        assert entries[0].text == "Hello, world!"
        assert entries[0].start_ms == 1000
        assert entries[0].end_ms == 4000
        assert entries[1].text == "How are you?"
        assert entries[1].start_ms == 5000
        assert entries[1].end_ms == 8500

    def test_parse_srt_with_html_tags(self):
        srt = """1
00:01:00,000 --> 00:01:03,000
<i>This is italic</i>
"""
        entries = self.engine._parse_srt(srt)
        assert len(entries) == 1
        assert entries[0].text == "This is italic"

    def test_parse_srt_multiline_text(self):
        srt = """1
00:00:01,000 --> 00:00:04,000
Line one
Line two
"""
        entries = self.engine._parse_srt(srt)
        assert len(entries) == 1
        assert entries[0].text == "Line one Line two"

    def test_parse_srt_empty(self):
        entries = self.engine._parse_srt("")
        assert len(entries) == 0

    def test_parse_srt_invalid_format(self):
        srt = "this is not valid srt content"
        entries = self.engine._parse_srt(srt)
        assert len(entries) == 0

    def test_identify_clip_candidates(self):
        from app.services.clip_engine import SubtitleEntry, SceneChange

        subtitles = [
            SubtitleEntry(1, 5000, 8000, "I'll be back"),
            SubtitleEntry(2, 60000, 63000, "May the force be with you"),
        ]
        scene_changes = [
            SceneChange(4000, 0.5),
            SceneChange(9000, 0.4),
            SceneChange(59000, 0.6),
            SceneChange(64000, 0.5),
        ]
        audio_energy = [
            {"time_ms": 6000, "rms_db": -20.0},
            {"time_ms": 61000, "rms_db": -10.0},
        ]

        candidates = self.engine.identify_clip_candidates(
            subtitles, scene_changes, audio_energy,
            total_duration_ms=120000,
            popular_quotes=["I'll be back", "May the force be with you"],
        )
        assert len(candidates) == 2
        assert candidates[0].quote_match_score > 0.5
        assert candidates[1].quote_match_score > 0.5

    def test_identify_clip_candidates_no_quotes(self):
        from app.services.clip_engine import SubtitleEntry

        subtitles = [
            SubtitleEntry(1, 5000, 8000, "Just a regular line"),
        ]

        candidates = self.engine.identify_clip_candidates(
            subtitles, [], [], total_duration_ms=120000
        )
        assert len(candidates) == 1
        assert candidates[0].quote_match_score == 0.0

    def test_identify_clip_candidates_empty(self):
        candidates = self.engine.identify_clip_candidates([], [], [], 120000)
        assert len(candidates) == 0
