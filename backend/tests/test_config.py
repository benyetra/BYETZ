from app.config import Settings


class TestConfig:
    def test_default_settings(self):
        s = Settings()
        assert s.app_name == "BYETZ"
        assert s.min_clip_duration_ms == 8000
        assert s.max_clip_duration_ms == 30000
        assert s.exploration_rate == 0.20
        assert s.max_consecutive_same_title == 2
        assert s.max_genre_ratio == 0.40
        assert s.cold_start_threshold == 50
        assert s.clips_per_movie == 10
        assert s.clips_per_episode == 5

    def test_clip_duration_bounds(self):
        s = Settings()
        assert s.min_clip_duration_ms >= 8000
        assert s.max_clip_duration_ms <= 30000
        assert s.min_clip_duration_ms < s.max_clip_duration_ms
