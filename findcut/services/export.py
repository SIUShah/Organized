from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from findcut.domain.models import ExportSettings, Project
from findcut.media.ffmpeg import FFmpegAdapter


@dataclass
class ExportJob:
    input_path: Path
    output_path: Path
    settings: ExportSettings


class ExportService:
    def __init__(self, media: FFmpegAdapter | None = None) -> None:
        self.media = media or FFmpegAdapter()

    def make_job(self, project: Project, output_path: str | Path) -> ExportJob:
        if not project.media:
            raise ValueError("The project has no media.")
        return ExportJob(Path(project.media[0].path), Path(output_path), project.export)

    def run(self, job: ExportJob) -> None:
        self.media.export(job.input_path, job.output_path, job.settings)
