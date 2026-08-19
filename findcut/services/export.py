from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from findcut.domain.models import Clip, ExportSettings, Project
from findcut.media.ffmpeg import FFmpegAdapter
from findcut.media.renderer import TimelineRenderer


@dataclass
class ExportJob:
    input_path: Path
    output_path: Path
    settings: ExportSettings
    source_in: float = 0.0
    source_duration: float | None = None


class ExportService:
    def __init__(self, media: FFmpegAdapter | None = None) -> None:
        self.media = media or FFmpegAdapter()
        self.renderer = TimelineRenderer(self.media)

    def make_job(self, project: Project, output_path: str | Path, clip: Clip | None = None) -> ExportJob:
        if not project.media:
            raise ValueError("The project has no media.")
        asset = next((a for a in project.media if clip and a.id == clip.asset_id), project.media[0])
        duration = clip.duration if clip and clip.source_out is not None else None
        source_in = clip.source_in if clip else 0.0
        return ExportJob(Path(asset.path), Path(output_path), project.export, source_in, duration)

    def run(self, job: ExportJob) -> None:
        job.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.media.export(job.input_path, job.output_path, job.settings, job.source_in, job.source_duration)

    def extract_audio(self, input_path: str | Path, output_path: str | Path, start: float = 0.0, duration: float | None = None) -> None:
        self.media.extract_audio(input_path, output_path, start, duration)

    def render_project(self, project: Project, output_path: str | Path) -> None:
        self.renderer.render(project, output_path)
