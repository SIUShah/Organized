from __future__ import annotations

from dataclasses import dataclass

from findcut.domain.models import ExportSettings, Project


@dataclass(frozen=True)
class ProjectTemplate:
    key: str
    name: str
    description: str
    export: ExportSettings


TEMPLATES = (
    ProjectTemplate("youtube-1080p", "YouTube 1080p", "16:9 long-form video with AAC audio.", ExportSettings(width=1920, height=1080, fps=30.0, video_bitrate="8M")),
    ProjectTemplate("shorts-vertical", "Shorts / Reels 1080x1920", "Vertical short-form video template.", ExportSettings(width=1080, height=1920, fps=30.0, video_bitrate="8M")),
    ProjectTemplate("podcast", "Podcast Video", "16:9 talking-head and audio-first template.", ExportSettings(width=1920, height=1080, fps=30.0, video_bitrate="6M", audio_bitrate="256k")),
    ProjectTemplate("slideshow", "Photo Slideshow", "16:9 image and music composition template.", ExportSettings(width=1920, height=1080, fps=30.0, video_bitrate="8M")),
)


def available_templates() -> tuple[ProjectTemplate, ...]:
    return TEMPLATES


def create_from_template(key: str) -> Project:
    template = next((item for item in TEMPLATES if item.key == key), None)
    if template is None:
        raise ValueError(f"Unknown project template: {key}")
    return Project(name=template.name, export=template.export)
