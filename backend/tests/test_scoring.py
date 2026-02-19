import pytest
from app.services.scoring import ClipScoringService, ClipCandidate


class TestClipScoringService:
    def setup_method(self):
        self.scoring = ClipScoringService()

    def test_compute_composite_score_all_zeros(self):
        candidate = ClipCandidate(
            start_ms=0, end_ms=10000, duration_ms=10000,
            quote_match_score=0.0,
            audio_energy_score=0.0,
            scene_composition_score=0.0,
            dialogue_density_score=0.0,
            temporal_position_score=0.0,
        )
        score = self.scoring.compute_composite_score(candidate)
        assert score == 0.0

    def test_compute_composite_score_all_ones(self):
        candidate = ClipCandidate(
            start_ms=0, end_ms=10000, duration_ms=10000,
            quote_match_score=1.0,
            audio_energy_score=1.0,
            scene_composition_score=1.0,
            dialogue_density_score=1.0,
            temporal_position_score=1.0,
        )
        score = self.scoring.compute_composite_score(candidate)
        # 0.35 + 0.20 + 0.15 + 0.15 + 0.10 = 0.95 (no AI vision in MVP)
        assert score == 0.95

    def test_compute_composite_score_mixed(self):
        candidate = ClipCandidate(
            start_ms=0, end_ms=15000, duration_ms=15000,
            quote_match_score=0.8,
            audio_energy_score=0.6,
            scene_composition_score=0.5,
            dialogue_density_score=0.7,
            temporal_position_score=0.9,
        )
        score = self.scoring.compute_composite_score(candidate)
        expected = 0.8 * 0.35 + 0.6 * 0.20 + 0.5 * 0.15 + 0.7 * 0.15 + 0.9 * 0.10
        assert score == round(expected, 4)

    def test_composite_score_clamped_to_max_1(self):
        candidate = ClipCandidate(
            start_ms=0, end_ms=10000, duration_ms=10000,
            quote_match_score=5.0,
            audio_energy_score=5.0,
            scene_composition_score=5.0,
            dialogue_density_score=5.0,
            temporal_position_score=5.0,
        )
        score = self.scoring.compute_composite_score(candidate)
        assert score == 1.0

    def test_composite_score_clamped_to_min_0(self):
        candidate = ClipCandidate(
            start_ms=0, end_ms=10000, duration_ms=10000,
            quote_match_score=-5.0,
            audio_energy_score=-5.0,
            scene_composition_score=-5.0,
            dialogue_density_score=-5.0,
            temporal_position_score=-5.0,
        )
        score = self.scoring.compute_composite_score(candidate)
        assert score == 0.0

    def test_temporal_position_climactic(self):
        score = self.scoring.compute_temporal_position_score(90000, 100000)
        assert score == 1.0

    def test_temporal_position_early(self):
        score = self.scoring.compute_temporal_position_score(5000, 100000)
        assert score == 0.2

    def test_temporal_position_middle(self):
        score = self.scoring.compute_temporal_position_score(50000, 100000)
        assert score == 0.5

    def test_temporal_position_zero_duration(self):
        score = self.scoring.compute_temporal_position_score(5000, 0)
        assert score == 0.0

    def test_dialogue_density_high(self):
        subs = [{"text": f"line {i}"} for i in range(10)]
        score = self.scoring.compute_dialogue_density_score(subs)
        assert score == 1.0

    def test_dialogue_density_medium(self):
        subs = [{"text": f"line {i}"} for i in range(5)]
        score = self.scoring.compute_dialogue_density_score(subs)
        assert score == 0.5

    def test_dialogue_density_low(self):
        subs = [{"text": "line"}]
        score = self.scoring.compute_dialogue_density_score(subs)
        assert score == 0.1

    def test_dialogue_density_empty(self):
        score = self.scoring.compute_dialogue_density_score([])
        assert score == 0.0

    def test_generate_content_embedding_dimension(self):
        embedding = self.scoring.generate_content_embedding(
            genre_tags=["Action", "Comedy"],
            actors=["Actor1"],
            director="Director1",
            decade="2020s",
            score_components={"quote_match": 0.5},
        )
        assert len(embedding) == 64

    def test_generate_content_embedding_normalized(self):
        embedding = self.scoring.generate_content_embedding(
            genre_tags=["Drama"],
            actors=[],
            director="",
            decade="",
            score_components={},
        )
        import numpy as np
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 0.01

    def test_rank_candidates(self):
        candidates = [
            ClipCandidate(0, 10000, 10000, quote_match_score=0.2),
            ClipCandidate(10000, 20000, 10000, quote_match_score=0.9),
            ClipCandidate(20000, 30000, 10000, quote_match_score=0.5),
        ]
        ranked = self.scoring.rank_candidates(candidates, max_clips=2)
        assert len(ranked) == 2
        assert ranked[0].quote_match_score == 0.9
        assert ranked[1].quote_match_score == 0.5

    def test_weights_sum(self):
        total = sum(self.scoring.WEIGHTS.values())
        assert abs(total - 0.95) < 0.01  # 5% reserved for AI vision (v2)
