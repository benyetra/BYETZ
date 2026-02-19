import numpy as np
from dataclasses import dataclass


@dataclass
class ClipCandidate:
    start_ms: int
    end_ms: int
    duration_ms: int
    quote_match_score: float = 0.0
    audio_energy_score: float = 0.0
    scene_composition_score: float = 0.0
    dialogue_density_score: float = 0.0
    temporal_position_score: float = 0.0


class ClipScoringService:
    WEIGHTS = {
        "quote_match": 0.35,
        "audio_energy": 0.20,
        "scene_composition": 0.15,
        "dialogue_density": 0.15,
        "temporal_position": 0.10,
    }

    def compute_composite_score(self, candidate: ClipCandidate) -> float:
        score = (
            candidate.quote_match_score * self.WEIGHTS["quote_match"]
            + candidate.audio_energy_score * self.WEIGHTS["audio_energy"]
            + candidate.scene_composition_score * self.WEIGHTS["scene_composition"]
            + candidate.dialogue_density_score * self.WEIGHTS["dialogue_density"]
            + candidate.temporal_position_score * self.WEIGHTS["temporal_position"]
        )
        return round(min(max(score, 0.0), 1.0), 4)

    def compute_temporal_position_score(self, position_ms: int, total_duration_ms: int) -> float:
        if total_duration_ms <= 0:
            return 0.0
        position_ratio = position_ms / total_duration_ms
        if position_ratio >= 0.80:
            return 1.0
        elif position_ratio >= 0.60:
            return 0.7
        elif position_ratio >= 0.40:
            return 0.5
        elif position_ratio >= 0.20:
            return 0.3
        return 0.2

    def compute_dialogue_density_score(self, subtitle_entries: list[dict], window_ms: int = 30000) -> float:
        if not subtitle_entries:
            return 0.0
        count = len(subtitle_entries)
        if count >= 10:
            return 1.0
        elif count >= 7:
            return 0.8
        elif count >= 4:
            return 0.5
        elif count >= 2:
            return 0.3
        return 0.1

    def generate_content_embedding(
        self, genre_tags: list[str], actors: list[str],
        director: str, decade: str, score_components: dict,
    ) -> list[float]:
        np.random.seed(hash(str(genre_tags) + str(actors) + str(director) + str(decade)) % 2**32)
        embedding = np.random.randn(64).tolist()
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = [x / norm for x in embedding]
        return embedding

    def rank_candidates(self, candidates: list[ClipCandidate], max_clips: int) -> list[ClipCandidate]:
        for c in candidates:
            c.composite_score = self.compute_composite_score(c)
        candidates.sort(key=lambda c: c.composite_score, reverse=True)
        return candidates[:max_clips]
