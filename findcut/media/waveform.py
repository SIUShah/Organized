from __future__ import annotations

from pathlib import Path
import subprocess

from findcut.media.ffmpeg import FFmpegAdapter, MediaError


class WaveformRenderer:
    """Generate deterministic waveform artwork using FFmpeg's showwavespic filter."""

    def __init__(self, media: FFmpegAdapter | None = None) -> None:
        self.media = media or FFmpegAdapter()

    def render(self, source: str | Path, output: str | Path, width: int = 1400, height: int = 240) -> Path:
        source_path = Path(source)
        if not source_path.exists():
            raise MediaError("Audio source not found.")
        target = Path(output)
        target.parent.mkdir(parents=True, exist_ok=True)
        command = [
            self.media.ffmpeg_path,
            "-y",
            "-i", str(source_path),
            "-filter_complex", f"aformat=channel_layouts=stereo,showwavespic=s={int(width)}x{int(height)}:colors=#67e8f9|#a78bfa:scale=sqrt",
            "-frames:v", "1",
            "-an",
            str(target),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0 or not target.exists():
            raise MediaError("Waveform generation failed. See FFmpeg details in the log.")
        return target
