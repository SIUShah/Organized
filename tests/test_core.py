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


def test_whisper_srt_formatting_and_model_manager(tmp_path: Path):
    from findcut.ai.model_manager import ModelManager
    from findcut.ai.transcription import write_srt

    manager = ModelManager(tmp_path / "models")
    assert {item.name for item in manager.available()} >= {"tiny", "base", "turbo"}
    assert not manager.is_installed("tiny")
    target = write_srt([{"start": 1.25, "end": 3.5, "text": "Hello FindCut"}], tmp_path / "captions.srt")
    assert target.read_text(encoding="utf-8") == "1\n00:00:01,250 --> 00:00:03,500\nHello FindCut\n"


def test_timeline_renderer_mixes_audio_and_layers_video(tmp_path: Path):
    from findcut.media.renderer import TimelineRenderer
    from findcut.domain.models import Track

    video = tmp_path / "video.mp4"
    audio = tmp_path / "voice.wav"
    output = tmp_path / "mixed.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=green:s=160x120:d=1", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-shortest", "-pix_fmt", "yuv420p", str(video)], capture_output=True, check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=0.6", str(audio)], capture_output=True, check=True)
    project = Project()
    video_asset = project.add_asset(str(video), "video", duration=1.0, width=160, height=120, fps=25.0)
    audio_asset = project.add_asset(str(audio), "audio", duration=0.6, sample_rate=44100, channels=1)
    video_track = next(track for track in project.tracks if track.kind == "video")
    audio_track = next(track for track in project.tracks if track.kind == "audio")
    project.add_clip(video_asset.id, video_track.id, 0.0, 0.0, 1.0)
    project.add_clip(audio_asset.id, audio_track.id, 0.2, 0.0, 0.6)
    TimelineRenderer().render(project, output)
    probe = FFmpegAdapter().probe(output)
    assert output.exists()
    assert probe.duration > 0.8


def test_timeline_snapping_and_track_creation():
    from findcut.services.timeline import TimelineService

    project = Project()
    asset = project.add_asset("sample.mp4", "video", duration=10.0)
    track = next(track for track in project.tracks if track.kind == "video")
    first = project.add_clip(asset.id, track.id, 0.0, 0.0, 2.0)
    second = project.add_clip(asset.id, track.id, 3.0, 0.0, 2.0)
    service = TimelineService(project, snap_threshold=0.2)
    service.move(second.id, 2.08)
    assert second.timeline_start == 2.0
    added = service.add_track("video")
    assert added.kind == "video"
    service.move(first.id, 0.5, track_id=added.id)
    assert first.track_id == added.id


def test_fade_transition_requires_adjacent_video_clips():
    from findcut.services.timeline import TimelineService

    project = Project()
    asset = project.add_asset("sample.mp4", "video", duration=10.0)
    track = next(track for track in project.tracks if track.kind == "video")
    left = project.add_clip(asset.id, track.id, 0.0, 0.0, 2.0)
    right = project.add_clip(asset.id, track.id, 2.0, 2.0, 4.0)
    transition = TimelineService(project).add_transition(left.id, right.id, duration=0.4)
    assert transition.kind == "fade"
    assert transition.duration == 0.4

def test_keyframes_are_sorted_and_serializable():
    from findcut.services.timeline import TimelineService

    project = Project()
    asset = project.add_asset("sample.mp4", "video", duration=4.0)
    track = next(track for track in project.tracks if track.kind == "video")
    clip = project.add_clip(asset.id, track.id, 0.0, 0.0, 4.0)
    service = TimelineService(project)
    assert service.set_keyframe(clip.id, "opacity", 3.0, 0.2) == [(3.0, 0.2)]
    assert service.set_keyframe(clip.id, "opacity", 0.0, 1.0) == [(0.0, 1.0), (3.0, 0.2)]
    restored = Project.from_dict(project.to_dict())
    assert restored.tracks[0].clips[0].keyframes["opacity"] == [[0.0, 1.0], [3.0, 0.2]] or restored.tracks[0].clips[0].keyframes["opacity"] == [(0.0, 1.0), (3.0, 0.2)]


def test_keyframe_expression_contains_piecewise_interpolation():
    from findcut.media.renderer import TimelineRenderer

    expression = TimelineRenderer._keyframe_expression([(0.0, 1.0), (2.0, 0.0)], 1.0)
    assert "lt(t" in expression
    assert "0.000000" in expression


def test_waveform_renderer_generates_png(tmp_path: Path):
    from findcut.media.waveform import WaveformRenderer

    source = tmp_path / "tone.wav"
    output = tmp_path / "tone-waveform.png"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=0.4", str(source)], capture_output=True, check=True)
    result = WaveformRenderer().render(source, output, width=320, height=80)
    assert result == output
    assert output.exists()
    assert output.stat().st_size > 100


def test_audio_level_analyzer_reports_real_levels(tmp_path: Path):
    from findcut.media.levels import AudioLevelAnalyzer

    source = tmp_path / "tone.wav"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=0.4", str(source)], capture_output=True, check=True)
    levels = AudioLevelAnalyzer().analyze(source)
    assert levels.mean_db < 0
    assert levels.peak_db < 0
    assert levels.peak_db >= levels.mean_db


def test_media_engine_registry_has_safe_fallback():
    from findcut.media.engines import MediaEngineRegistry

    registry = MediaEngineRegistry()
    statuses = registry.statuses()
    assert statuses[0].name == "FFmpeg CLI"
    assert statuses[0].available is True
    assert registry.preferred().name in {"FFmpeg CLI", "libopenshot", "GStreamer Editing Services"}


def test_media_analyzer_detects_silence_and_scenes(tmp_path: Path):
    from findcut.media.analysis import MediaAnalyzer

    audio = tmp_path / "speech-gaps.wav"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=0.8", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-filter_complex", "[1:a]atrim=duration=0.5[s];[0:a][s]concat=n=2:v=0:a=1", "-t", "1.3", str(audio)], capture_output=True, check=True)
    silence = MediaAnalyzer().detect_silence(audio, min_duration=0.25)
    assert silence
    assert silence[0].duration >= 0.25

    video = tmp_path / "scenes.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=red:s=160x120:d=0.5", "-f", "lavfi", "-i", "color=c=blue:s=160x120:d=0.5", "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0", "-pix_fmt", "yuv420p", str(video)], capture_output=True, check=True)
    markers = MediaAnalyzer().detect_scenes(video, threshold=0.1)
    assert markers


def test_remove_silence_keeps_content_and_closes_timeline_gaps():
    from findcut.services.timeline import TimelineService

    project = Project()
    asset = project.add_asset("speech.wav", "audio", duration=5.0)
    track = next(track for track in project.tracks if track.kind == "audio")
    clip = project.add_clip(asset.id, track.id, 0.0, 0.0, 5.0)
    replacement = TimelineService(project).remove_silence(clip.id, [(1.0, 2.0), (3.0, 3.5)], padding=0.0)
    assert len(replacement) == 3
    assert replacement[0].timeline_start == 0.0
    assert replacement[1].timeline_start == replacement[0].duration
