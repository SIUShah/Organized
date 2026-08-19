from pathlib import Path
import json
import subprocess

import pytest

from findcut.domain.models import Project
from findcut.media.ffmpeg import FFmpegAdapter, MediaError


def test_project_creation_has_default_tracks():
    project = Project()
    assert {track.kind for track in project.tracks} == {"video", "audio"}


def test_project_save_and_load_round_trip(tmp_path: Path):
    project = Project(name="Creator Project")
    asset = project.add_asset("sample.mp4", "video", duration=10.0, width=1920, height=1080, fps=30.0)
    track = next(track for track in project.tracks if track.kind == "video")
    project.add_clip(asset.id, track.id, start=2.0, source_in=1.0, source_out=5.0)
    path = tmp_path / "project.findcut"
    project.save(path)
    loaded = Project.load(path)
    assert loaded.name == "Creator Project"
    assert loaded.media[0].path == "sample.mp4"
    assert loaded.tracks[0].clips or loaded.tracks[1].clips


def test_clip_duration_and_split_style_trim():
    project = Project()
    asset = project.add_asset("sample.mp4", "video", duration=20.0)
    track = next(track for track in project.tracks if track.kind == "video")
    clip = project.add_clip(asset.id, track.id, source_in=2.0, source_out=12.0)
    assert clip.duration == 10.0
    clip.source_out = 8.0
    assert clip.duration == 6.0


def test_invalid_project_schema_is_rejected(tmp_path: Path):
    path = tmp_path / "bad.findcut"
    path.write_text(json.dumps({"schema_version": 999}), encoding="utf-8")
    with pytest.raises(ValueError):
        Project.load(path)


def test_probe_missing_media_is_user_safe(tmp_path: Path):
    with pytest.raises(MediaError, match="Media file not found"):
        FFmpegAdapter().probe(tmp_path / "missing.mp4")


def test_probe_real_sample(tmp_path: Path):
    source = tmp_path / "sample.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=blue:s=320x240:d=1", "-pix_fmt", "yuv420p", str(source)], capture_output=True, check=True)
    result = FFmpegAdapter().probe(source)
    assert result.kind == "video"
    assert result.width == 320
    assert result.height == 240
    assert result.duration > 0


def test_timeline_split_trim_move_delete():
    from findcut.services.timeline import TimelineService

    project = Project()
    asset = project.add_asset("sample.mp4", "video", duration=20.0)
    track = next(track for track in project.tracks if track.kind == "video")
    clip = project.add_clip(asset.id, track.id, start=0.0, source_in=0.0, source_out=10.0)
    service = TimelineService(project)
    service.trim(clip.id, source_in=1.0, source_out=9.0)
    left, right = service.split(clip.id, timeline_position=4.0)
    assert left.duration == 4.0
    assert right.timeline_start == 4.0
    service.move(right.id, 5.0)
    assert right.timeline_start == 5.0
    service.delete(left.id)
    assert all(item.id != left.id for item in track.clips)


def test_timeline_renderer_composes_multiple_clips(tmp_path: Path):
    from findcut.media.renderer import TimelineRenderer

    first = tmp_path / "first.mp4"
    second = tmp_path / "second.mp4"
    output = tmp_path / "edited.mp4"
    for target, color in ((first, "red"), (second, "blue")):
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={color}:s=160x120:d=0.5", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-shortest", "-pix_fmt", "yuv420p", str(target)], capture_output=True, check=True)
    project = Project()
    first_asset = project.add_asset(str(first), "video", duration=0.5, width=160, height=120, fps=25.0)
    second_asset = project.add_asset(str(second), "video", duration=0.5, width=160, height=120, fps=25.0)
    track = next(track for track in project.tracks if track.kind == "video")
    project.add_clip(first_asset.id, track.id, 0.0, 0.0, 0.5)
    project.add_clip(second_asset.id, track.id, 0.5, 0.0, 0.5)
    TimelineRenderer().render(project, output)
    probe = FFmpegAdapter().probe(output)
    assert output.exists()
    assert probe.kind == "video"
    assert probe.duration >= 0.8
