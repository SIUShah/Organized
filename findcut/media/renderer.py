from __future__ import annotations

from pathlib import Path
import logging
import subprocess

from findcut.domain.models import Project, Track
from findcut.media.ffmpeg import FFmpegAdapter, MediaError

logger = logging.getLogger(__name__)


class TimelineRenderer:
    """Render the current project model into a playable MP4 using FFmpeg filters."""

    def __init__(self, media: FFmpegAdapter | None = None) -> None:
        self.media = media or FFmpegAdapter()

    def render(self, project: Project, output_path: str | Path) -> None:
        video_track = next((track for track in project.tracks if track.kind == "video" and track.clips), None)
        audio_track = next((track for track in project.tracks if track.kind == "audio" and track.clips), None)
        if not video_track and not audio_track:
            raise ValueError("The timeline has no clips.")

        inputs: list[str] = []
        filters: list[str] = []
        video_labels: list[str] = []
        audio_labels: list[str] = []
        clip_index = 0

        if video_track:
            for clip in sorted(video_track.clips, key=lambda item: item.timeline_start):
                asset = self._asset(project, clip.asset_id)
                if asset.kind not in {"video", "image"}:
                    continue
                inputs.extend(["-i", asset.path])
                end = clip.source_out if clip.source_out is not None else asset.duration
                if asset.kind == "image":
                    filters.append(f"[{clip_index}:v]scale={project.export.width}:{project.export.height}:force_original_aspect_ratio=decrease,pad={project.export.width}:{project.export.height}:(ow-iw)/2:(oh-ih)/2,trim=duration={max(0.1, clip.duration):.6f},setpts=PTS-STARTPTS[v{clip_index}]")
                else:
                    filters.append(f"[{clip_index}:v]trim=start={clip.source_in:.6f}:end={end:.6f},setpts=PTS-STARTPTS,scale={project.export.width}:{project.export.height}:force_original_aspect_ratio=decrease,pad={project.export.width}:{project.export.height}:(ow-iw)/2:(oh-ih)/2[v{clip_index}]")
                video_labels.append(f"[v{clip_index}]")
                clip_index += 1

        if audio_track:
            for clip in sorted(audio_track.clips, key=lambda item: item.timeline_start):
                asset = self._asset(project, clip.asset_id)
                if asset.kind not in {"video", "audio"}:
                    continue
                inputs.extend(["-i", asset.path])
                end = clip.source_out if clip.source_out is not None else asset.duration
                filters.append(f"[{clip_index}:a]atrim=start={clip.source_in:.6f}:end={end:.6f},asetpts=PTS-STARTPTS,volume={max(0.0, clip.volume):.4f}[a{clip_index}]")
                audio_labels.append(f"[a{clip_index}]")
                clip_index += 1

        if not video_labels and not audio_labels:
            raise ValueError("The timeline contains no renderable media clips.")
        if len(video_labels) == 1:
            filters.append(f"{video_labels[0]}null[vout]")
        elif video_labels:
            filters.append("".join(video_labels) + f"concat=n={len(video_labels)}:v=1:a=0[vout]")
        if len(audio_labels) == 1:
            filters.append(f"{audio_labels[0]}anull[aout]")
        elif audio_labels:
            filters.append("".join(audio_labels) + f"concat=n={len(audio_labels)}:v=0:a=1[aout]")

        command = [self.media.ffmpeg_path, "-y", *inputs, "-filter_complex", ";".join(filters)]
        if video_labels:
            command.extend(["-map", "[vout]", "-c:v", project.export.video_codec, "-b:v", project.export.video_bitrate, "-r", str(project.export.fps)])
        if audio_labels:
            command.extend(["-map", "[aout]", "-c:a", project.export.audio_codec, "-b:a", project.export.audio_bitrate])
        else:
            command.append("-an")
        command.extend(["-movflags", "+faststart", str(output_path)])
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            logger.error("Timeline render failed: %s", completed.stderr.strip())
            raise MediaError("Timeline render failed. See details.")

    @staticmethod
    def _asset(project: Project, asset_id: str):
        asset = next((item for item in project.media if item.id == asset_id), None)
        if asset is None or not Path(asset.path).exists():
            raise MediaError("Media file not found.")
        return asset
