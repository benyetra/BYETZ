import os
import subprocess
import json
import re
from dataclasses import dataclass
from app.config import get_settings
from app.services.scoring import ClipScoringService, ClipCandidate

settings = get_settings()


@dataclass
class SubtitleEntry:
    index: int
    start_ms: int
    end_ms: int
    text: str


@dataclass
class SceneChange:
    timestamp_ms: int
    score: float


class ClipEngine:
    def __init__(self):
        self.scoring = ClipScoringService()

    def extract_subtitles(self, media_path: str) -> list[SubtitleEntry]:
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json",
                 "-show_entries", "stream=index,codec_type,codec_name", media_path],
                capture_output=True, text=True, timeout=30,
            )
            streams = json.loads(result.stdout).get("streams", [])
            sub_stream = next((s for s in streams if s.get("codec_type") == "subtitle"), None)
            if not sub_stream:
                return []

            sub_index = sub_stream["index"]
            result = subprocess.run(
                ["ffmpeg", "-i", media_path, "-map", f"0:{sub_index}", "-f", "srt", "-"],
                capture_output=True, text=True, timeout=120,
            )
            return self._parse_srt(result.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return []

    def _parse_srt(self, srt_text: str) -> list[SubtitleEntry]:
        entries = []
        blocks = re.split(r"\n\n+", srt_text.strip())
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue
            try:
                index = int(lines[0])
                time_match = re.match(
                    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})",
                    lines[1],
                )
                if not time_match:
                    continue
                g = time_match.groups()
                start_ms = (int(g[0]) * 3600 + int(g[1]) * 60 + int(g[2])) * 1000 + int(g[3])
                end_ms = (int(g[4]) * 3600 + int(g[5]) * 60 + int(g[6])) * 1000 + int(g[7])
                text = " ".join(lines[2:]).strip()
                text = re.sub(r"<[^>]+>", "", text)
                entries.append(SubtitleEntry(index=index, start_ms=start_ms, end_ms=end_ms, text=text))
            except (ValueError, IndexError):
                continue
        return entries

    def detect_scene_changes(self, media_path: str, threshold: float = 0.3) -> list[SceneChange]:
        try:
            result = subprocess.run(
                ["ffmpeg", "-i", media_path,
                 "-filter:v", f"select='gt(scene,{threshold})',showinfo",
                 "-f", "null", "-"],
                capture_output=True, text=True, timeout=600,
            )
            scenes = []
            for line in result.stderr.split("\n"):
                if "showinfo" in line and "pts_time:" in line:
                    time_match = re.search(r"pts_time:(\d+\.?\d*)", line)
                    if time_match:
                        ts_ms = int(float(time_match.group(1)) * 1000)
                        scenes.append(SceneChange(timestamp_ms=ts_ms, score=threshold))
            return scenes
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []

    def analyze_audio_energy(self, media_path: str) -> list[dict]:
        try:
            result = subprocess.run(
                ["ffmpeg", "-i", media_path,
                 "-af", "astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level",
                 "-f", "null", "-"],
                capture_output=True, text=True, timeout=600,
            )
            energy_data = []
            current_time = 0.0
            for line in result.stderr.split("\n"):
                time_match = re.search(r"pts_time:(\d+\.?\d*)", line)
                if time_match:
                    current_time = float(time_match.group(1))
                rms_match = re.search(r"RMS_level=(-?\d+\.?\d*)", line)
                if rms_match:
                    rms = float(rms_match.group(1))
                    energy_data.append({"time_ms": int(current_time * 1000), "rms_db": rms})
            return energy_data
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []

    def identify_clip_candidates(
        self, subtitles: list[SubtitleEntry], scene_changes: list[SceneChange],
        audio_energy: list[dict], total_duration_ms: int,
        popular_quotes: list[str] = None,
    ) -> list[ClipCandidate]:
        candidates = []

        for sub in subtitles:
            quote_score = 0.0
            if popular_quotes:
                text_lower = sub.text.lower().strip()
                for quote in popular_quotes:
                    if quote.lower() in text_lower or text_lower in quote.lower():
                        quote_score = max(quote_score, 0.9)
                        break

            start = max(0, sub.start_ms - 2000)
            end = min(total_duration_ms, sub.end_ms + 2000)

            nearest_scene_before = max(
                (sc.timestamp_ms for sc in scene_changes if sc.timestamp_ms <= start),
                default=start,
            )
            nearest_scene_after = min(
                (sc.timestamp_ms for sc in scene_changes if sc.timestamp_ms >= end),
                default=end,
            )

            clip_start = nearest_scene_before
            clip_end = nearest_scene_after
            duration = clip_end - clip_start

            if duration < settings.min_clip_duration_ms:
                clip_end = clip_start + settings.min_clip_duration_ms
            elif duration > settings.max_clip_duration_ms:
                clip_end = clip_start + settings.max_clip_duration_ms

            duration = clip_end - clip_start

            nearby_subs = [s for s in subtitles if s.start_ms >= clip_start and s.end_ms <= clip_end]
            dialogue_score = self.scoring.compute_dialogue_density_score(
                [{"text": s.text} for s in nearby_subs]
            )
            temporal_score = self.scoring.compute_temporal_position_score(clip_start, total_duration_ms)

            audio_score = 0.5
            if audio_energy:
                nearby_energy = [e for e in audio_energy if clip_start <= e["time_ms"] <= clip_end]
                if nearby_energy:
                    max_rms = max(e["rms_db"] for e in nearby_energy)
                    audio_score = min(1.0, max(0.0, (max_rms + 60) / 60))

            scene_density = len([sc for sc in scene_changes if clip_start <= sc.timestamp_ms <= clip_end])
            scene_score = min(1.0, scene_density / 5.0)

            candidate = ClipCandidate(
                start_ms=clip_start, end_ms=clip_end, duration_ms=duration,
                quote_match_score=quote_score, audio_energy_score=audio_score,
                scene_composition_score=scene_score, dialogue_density_score=dialogue_score,
                temporal_position_score=temporal_score,
            )
            candidates.append(candidate)

        return candidates

    def extract_clip(self, media_path: str, output_path: str, start_ms: int, end_ms: int) -> bool:
        start_sec = start_ms / 1000.0
        duration_sec = (end_ms - start_ms) / 1000.0
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            subprocess.run(
                ["ffmpeg", "-y", "-ss", str(start_sec), "-i", media_path,
                 "-t", str(duration_sec),
                 "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                 "-c:a", "aac", "-b:a", "128k",
                 "-af", f"afade=t=in:st=0:d=0.5,afade=t=out:st={duration_sec - 1.0}:d=1.0,"
                        f"loudnorm=I=-16:TP=-1.5:LRA=11",
                 "-movflags", "+faststart", output_path],
                capture_output=True, timeout=120, check=True,
            )
            return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False

    def generate_thumbnails(self, media_path: str, output_dir: str, timestamps_ms: list[int]) -> list[str]:
        paths = []
        os.makedirs(output_dir, exist_ok=True)
        for i, ts in enumerate(timestamps_ms[:3]):
            out = os.path.join(output_dir, f"thumb_{i}.jpg")
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-ss", str(ts / 1000.0), "-i", media_path,
                     "-vframes", "1", "-q:v", "2", out],
                    capture_output=True, timeout=30, check=True,
                )
                paths.append(out)
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                pass
        return paths
