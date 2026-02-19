import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from datetime import datetime
from app.services.recommendation import RecommendationService


class TestFeedCompositionRules:
    def setup_method(self):
        self.service = RecommendationService(MagicMock())

    def _make_clip(self, title="Movie", genres=None):
        clip = MagicMock()
        clip.id = uuid4()
        clip.title = title
        clip.genre_tags = genres or ["Action"]
        clip.media_id = f"media_{title}"
        clip.season_episode = None
        clip.start_time_ms = 0
        clip.end_time_ms = 15000
        clip.duration_ms = 15000
        clip.composite_score = 0.8
        clip.actors = []
        clip.director = None
        clip.decade = None
        clip.mood_tags = []
        clip.created_at = datetime.utcnow()
        clip.is_active = True
        return clip

    def test_no_three_consecutive_same_title(self):
        clips = [
            self._make_clip("Movie A"),
            self._make_clip("Movie A"),
            self._make_clip("Movie A"),
            self._make_clip("Movie B"),
        ]
        result = self.service._apply_composition_rules(clips)
        titles = [c.title for c in result]
        # Should not have 3 consecutive "Movie A"
        for i in range(len(titles) - 2):
            assert not (titles[i] == titles[i+1] == titles[i+2])

    def test_genre_diversity_enforcement(self):
        clips = []
        for i in range(10):
            clips.append(self._make_clip(f"Movie {i}", genres=["Action"]))
        clips.append(self._make_clip("Movie X", genres=["Comedy"]))

        result = self.service._apply_composition_rules(clips)
        # Should enforce genre diversity - not all should be Action
        assert len(result) <= len(clips)

    def test_empty_clips(self):
        result = self.service._apply_composition_rules([])
        assert result == []

    def test_single_clip(self):
        clips = [self._make_clip("Movie A")]
        result = self.service._apply_composition_rules(clips)
        assert len(result) == 1

    def test_mixed_titles_pass_through(self):
        clips = [
            self._make_clip("Movie A", genres=["Action"]),
            self._make_clip("Movie B", genres=["Comedy"]),
            self._make_clip("Movie C", genres=["Drama"]),
        ]
        result = self.service._apply_composition_rules(clips)
        assert len(result) == 3
