from __future__ import annotations

from pathlib import Path
import logging
import subprocess

from findcut.domain.models import Clip, Project, Track
from findcut.media.ffmpeg import FFmpegAdapter, MediaError

logger = logging.getLogger(__name__)


class TimelineRenderer:
    """Render a project timeline through FFmpeg's real compositor and mixer.

    Each video clip is positioned on the project clock and overlaid in track
    order. Audio clips are trimmed, delayed to their timeline positions, and
    mixed. The project model remains non-destructive; rendering creates a new
    media file.
    """

    def __init__(self, media: FFmpegAdapter | None = None) -> None:
        self.media = media or FFmpegAdapter()

    def render(self, project: Project, output_path: str | Path) -> None:
        video_tracks = [track for track in project.tracks if track.kind == "video" and track.clips and not track.muted]
        audio_tracks = [track for track in project.tracks if track.kind == "audio" and track.clips and not track.muted]
        if not video_tracks and not audio_tracks:
            raise ValueError("The timeline has no clips.")

        video_clips = [clip for track in video_tracks for clip in track.clips]
        audio_clips = [clip for track in audio_tracks for clip in track.clips if not clip.muted]
        duration = max((clip.timeline_start + clip.duration for clip in [*video_clips, *audio_clips]), default=0.0)
        if duration <= 0:
            raise ValueError("The timeline has no renderable duration.")

        inputs: list[str] = []
        filters: list[str] = []
        input_index = 0
        video_label = "base"
        width, height, fps = project.export.width, project.export.height, project.export.fps
        filters.append(f"color=c=black:s={width}x{height}:r={fps}:d={duration:.6f}[base]")

        for clip in sorted(video_clips, key=lambda item: (item.track_id, item.timeline_start)):
            asset = self._asset(project, clip.asset_id)
            if asset.kind not in {"video", "image"}:
                continue
            if asset.kind == "image":
                inputs.extend(["-loop", "1", "-i", asset.path])
            else:
                inputs.extend(["-i", asset.path])
            end = clip.source_out if clip.source_out is not None else asset.duration
            clip_duration = max(0.05, clip.duration)
            filters.append(
                f"[{input_index}:v]trim=start={clip.source_in:.6f}:end={end:.6f},"
                f"setpts=PTS-STARTPTS,scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
                f"trim=duration={clip_duration:.6f},setpts=PTS-STARTPTS[vclip{input_index}]"
            )
            start = max(0.0, clip.timeline_start)
            stop = start + clip_duration
            next_label = f"vcomp{input_index}"
            filters.append(
                f"[{video_label}][vclip{input_index}]overlay=0:0:eof_action=pass:"
                f"enable='between(t,{start:.6f},{stop:.6f})'[{next_label}]"
            )
            video_label = next_label
            input_index += 1

        audio_labels: list[str] = []
        for clip in sorted(audio_clips, key=lambda item: item.timeline_start):
            asset = self._asset(project, clip.asset_id)
            if asset.kind not in {"video", "audio"}:
                continue
            inputs.extend(["-i", asset.path])
            end = clip.source_out if clip.source_out is not None else asset.duration
            delay = max(0, int(round(clip.timeline_start * 1000)))
            volume = 0.0 if clip.muted else max(0.0, clip.volume)
            label = f"aclip{input_index}"
            filters.append(
                f"[{input_index}:a]atrim=start={clip.source_in:.6f}:end={end:.6f},"
                f"asetpts=PTS-STARTPTS,volume={volume:.4f},adelay={delay}|{delay}[{label}]"
            )
            audio_labels.append(f"[{label}]")
            input_index += 1

        if audio_labels:
            filters.append("".join(audio_labels) + f"amix=inputs={len(audio_labels)}:duration=longest:dropout_transition=0[aout]")

        command = [
            self.media.ffmpeg_path,
            "-y",
            *inputs,
            "-filter_complex",
            ";".join(filters),
            "-map",
            f"[{video_label}]",
            "-c:v",
            project.export.video_codec,
            "-b:v",
            project.export.video_bitrate,
            "-r",
            str(project.export.fps),
            "-t",
            f"{duration:.6f}",
        ]
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
