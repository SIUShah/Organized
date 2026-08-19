from __future__ import annotations

from findcut.domain.models import Clip, Project, new_id


class TimelineService:
    def __init__(self, project: Project) -> None:
        self.project = project

    def _find(self, clip_id: str) -> tuple[object, Clip]:
        for track in self.project.tracks:
            for clip in track.clips:
                if clip.id == clip_id:
                    return track, clip
        raise ValueError(f"Clip not found: {clip_id}")

    def trim(self, clip_id: str, source_in: float | None = None, source_out: float | None = None) -> Clip:
        _, clip = self._find(clip_id)
        if source_in is not None:
            clip.source_in = max(0.0, source_in)
        if source_out is not None:
            if source_out <= clip.source_in:
                raise ValueError("Trim end must be after trim start")
            clip.source_out = source_out
        return clip

    def split(self, clip_id: str, timeline_position: float) -> tuple[Clip, Clip]:
        track, clip = self._find(clip_id)
        if clip.source_out is None:
            raise ValueError("Cannot split a clip without a known duration")
        relative = (timeline_position - clip.timeline_start) * clip.speed
        if relative <= 0 or relative >= clip.source_out - clip.source_in:
            raise ValueError("Split position must be inside the clip")
        split_source = clip.source_in + relative
        left = Clip(new_id(), clip.asset_id, clip.track_id, clip.timeline_start, clip.source_in, split_source, clip.volume, clip.muted, clip.speed, clip.opacity, dict(clip.transform))
        right = Clip(new_id(), clip.asset_id, clip.track_id, timeline_position, split_source, clip.source_out, clip.volume, clip.muted, clip.speed, clip.opacity, dict(clip.transform))
        track.clips = [item for item in track.clips if item.id != clip_id] + [left, right]
        track.clips.sort(key=lambda item: item.timeline_start)
        return left, right

    def delete(self, clip_id: str) -> None:
        track, _ = self._find(clip_id)
        track.clips = [item for item in track.clips if item.id != clip_id]

    def move(self, clip_id: str, timeline_start: float) -> Clip:
        track, clip = self._find(clip_id)
        clip.timeline_start = max(0.0, timeline_start)
        track.clips.sort(key=lambda item: item.timeline_start)
        return clip
