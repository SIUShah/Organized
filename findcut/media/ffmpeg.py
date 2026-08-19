from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


class MediaError(RuntimeError):
    """A controlled media operation failure suitable for display to users."""


@dataclass
class ProbeResult:
    kind: str
    duration: float
    width: int
    height: int
    fps: float
    sample_rate: int
    channels: int
    metadata: dict


class FFmpegAdapter:
    def __init__(self, ffprobe_path: str | None = None, ffmpeg_path: str | None = None) -> None:
        self.ffprobe_path = ffprobe_path or self._bundled_binary("ffprobe") or shutil.which("ffprobe") or "ffprobe"
        self.ffmpeg_path = ffmpeg_path or self._bundled_binary("ffmpeg") or shutil.which("ffmpeg") or "ffmpeg"

    def probe(self, path: str | Path) -> ProbeResult:
        source = Path(path)
        if not source.exists():
            raise MediaError("Media file not found.")
        command = [self.ffprobe_path, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(source)]
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
        except OSError as exc:
            logger.exception("Could not launch ffprobe")
            raise MediaError("Media tools are not available.") from exc
        if completed.returncode != 0:
            logger.error("ffprobe failed for %s: %s", source, completed.stderr.strip())
            raise MediaError("This file could not be opened.")
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            logger.exception("Invalid ffprobe output for %s", source)
            raise MediaError("This file could not be opened.") from exc
        streams = payload.get("streams", [])
        video = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
        duration = float((payload.get("format") or {}).get("duration") or 0.0)
        fps = self._fraction((video or {}).get("r_frame_rate", "0/1"))
        kind = "video" if video else "audio" if audio else "unknown"
        return ProbeResult(
            kind=kind,
            duration=duration,
            width=int((video or {}).get("width") or 0),
            height=int((video or {}).get("height") or 0),
            fps=fps,
            sample_rate=int((audio or {}).get("sample_rate") or 0),
            channels=int((audio or {}).get("channels") or 0),
            metadata={"format": payload.get("format", {}), "streams": streams},
        )

    def export(self, input_path: str | Path, output_path: str | Path, settings, source_in: float = 0.0, source_duration: float | None = None, progress_callback=None) -> None:
        command = [self.ffmpeg_path, "-y"]
        if source_in > 0:
            command.extend(["-ss", f"{source_in:.6f}"])
        if source_duration is not None and source_duration > 0:
            command.extend(["-t", f"{source_duration:.6f}"])
        command.extend(["-i", str(input_path), "-c:v", settings.video_codec, "-c:a", settings.audio_codec, "-b:v", settings.video_bitrate, "-b:a", settings.audio_bitrate, "-r", str(settings.fps), "-s", f"{settings.width}x{settings.height}", str(output_path)])
        try:
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
        except OSError as exc:
            raise MediaError("Media tools are not available.") from exc
        if completed.returncode != 0:
            logger.error("Export failed: %s", completed.stderr.strip())
            raise MediaError("Export failed. See details.")

    def extract_audio(self, input_path: str | Path, output_path: str | Path, start: float = 0.0, duration: float | None = None) -> None:
        command = [self.ffmpeg_path, "-y"]
        if start > 0:
            command.extend(["-ss", f"{start:.6f}"])
        if duration is not None and duration > 0:
            command.extend(["-t", f"{duration:.6f}"])
        command.extend(["-i", str(input_path), "-vn", "-c:a", "aac", "-b:a", "192k", str(output_path)])
        try:
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
        except OSError as exc:
            logger.exception("Could not launch ffmpeg for audio extraction")
            raise MediaError("Media tools are not available.") from exc
        if completed.returncode != 0:
            logger.error("Audio extraction failed: %s", completed.stderr.strip())
            raise MediaError("Audio export failed. See details.")

    @staticmethod
    def _bundled_binary(name: str) -> str | None:
        candidates = []
        bundle_root = getattr(sys, "_MEIPASS", None)
        if bundle_root:
            candidates.append(Path(bundle_root) / "runtime" / f"{name}.exe")
        candidates.append(Path(sys.executable).resolve().parent / "runtime" / f"{name}.exe")
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return None

    @staticmethod
    def _fraction(value: str) -> float:
        try:
            numerator, denominator = value.split("/", 1)
            return float(numerator) / float(denominator)
        except (ValueError, ZeroDivisionError):
            return 0.0
