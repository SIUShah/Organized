from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess

from findcut.media.ffmpeg import FFmpegAdapter, MediaError


@dataclass(frozen=True)
class AudioLevels:
    mean_db: float
    peak_db: float


class AudioLevelAnalyzer:
    """Measure real media loudness values through FFmpeg's volumedetect filter."""

    def __init__(self, media: FFmpegAdapter | None = None) -> None:
        self.media = media or FFmpegAdapter()

    def analyze(self, source: str | Path) -> AudioLevels:
        source_path = Path(source)
        if not source_path.exists():
            raise MediaError("Audio source not found.")
        completed = subprocess.run(
            [self.media.ffmpeg_path, "-hide_banner", "-i", str(source_path), "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True, check=False,
        )
        report = f"{completed.stdout}\n{completed.stderr}"
        mean_match = re.search(r"mean_volume:\s*(-?inf|-?\d+(?:\.\d+)?) dB", report)
        peak_match = re.search(r"max_volume:\s*(-?inf|-?\d+(?:\.\d+)?) dB", report)
        if completed.returncode != 0 or not mean_match or not peak_match:
            raise MediaError("Audio level analysis failed.")
        def parse(value: str) -> float:
            return -60.0 if value == "-inf" else float(value)
        return AudioLevels(mean_db=parse(mean_match.group(1)), peak_db=parse(peak_match.group(1)))
