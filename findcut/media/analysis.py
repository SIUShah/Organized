from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess

from findcut.media.ffmpeg import FFmpegAdapter, MediaError


@dataclass(frozen=True)
class SilenceRange:
    start: float
    end: float

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass(frozen=True)
class SceneMarker:
    time: float
    score: float


class MediaAnalyzer:
    """Use FFmpeg's deterministic analysis filters for editorial decisions."""

    def __init__(self, media: FFmpegAdapter | None = None) -> None:
        self.media = media or FFmpegAdapter()

    def detect_silence(self, source: str | Path, noise_db: float = -35.0, min_duration: float = 0.35) -> list[SilenceRange]:
        path = Path(source)
        if not path.exists():
            raise MediaError("Media source not found.")
        command = [self.media.ffmpeg_path, "-hide_banner", "-i", str(path), "-af", f"silencedetect=noise={noise_db:.1f}dB:d={min_duration:.3f}", "-f", "null", "-"]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        report = f"{completed.stdout}\n{completed.stderr}"
        if completed.returncode != 0:
            raise MediaError("Silence detection failed.")
        starts = [float(value) for value in re.findall(r"silence_start:\s*(-?\d+(?:\.\d+)?)", report)]
        ends = [float(value) for value in re.findall(r"silence_end:\s*(-?\d+(?:\.\d+)?)", report)]
        ranges: list[SilenceRange] = []
        for index, start in enumerate(starts):
            if index < len(ends) and ends[index] > start:
                ranges.append(SilenceRange(start, ends[index]))
        return ranges

    def detect_scenes(self, source: str | Path, threshold: float = 0.35) -> list[SceneMarker]:
        path = Path(source)
        if not path.exists():
            raise MediaError("Media source not found.")
        command = [self.media.ffmpeg_path, "-hide_banner", "-i", str(path), "-vf", f"select='gt(scene,{threshold:.3f})',metadata=print:key=lavfi.scene_score,showinfo", "-an", "-f", "null", "-"]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        report = f"{completed.stdout}\n{completed.stderr}"
        if completed.returncode != 0:
            raise MediaError("Scene detection failed.")
        markers: list[SceneMarker] = []
        times = [float(value) for value in re.findall(r"pts_time:([0-9.]+)", report)]
        scores = [float(value) for value in re.findall(r"lavfi\.scene_score=([0-9.]+)", report)]
        for time, score in zip(times, scores):
            markers.append(SceneMarker(time, score))
        return markers
