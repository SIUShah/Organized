from __future__ import annotations

from findcut.domain.models import Clip, Project, Transition, new_id


class TimelineService:
    def __init__(self, project: Project, snap_threshold: float = 0.12) -> None:
        self.project = project
        self.snap_threshold = snap_threshold
        self.snapping_enabled = True

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

    def move(self, clip_id: str, timeline_start: float, track_id: str | None = None) -> Clip:
        old_track, clip = self._find(clip_id)
        target_track = old_track
        if track_id is not None:
            target_track = next((item for item in self.project.tracks if item.id == track_id), None)
            if target_track is None:
                raise ValueError(f"Track not found: {track_id}")
            if target_track.kind != old_track.kind:
                raise ValueError("A clip can only move between tracks of the same kind")
            if target_track is not old_track:
                old_track.clips = [item for item in old_track.clips if item.id != clip_id]
                target_track.clips.append(clip)
                clip.track_id = target_track.id
        requested = max(0.0, timeline_start)
        if self.snapping_enabled:
            requested = self.snap_position(clip_id, requested, target_track.id)
        clip.timeline_start = requested
        target_track.clips.sort(key=lambda item: item.timeline_start)
        return clip

    def snap_position(self, clip_id: str, timeline_start: float, track_id: str | None = None) -> float:
        """Snap a clip start to nearby clip boundaries or the project origin."""
        if not self.snapping_enabled:
            return max(0.0, timeline_start)
        candidates = [0.0]
        for track in self.project.tracks:
            if track_id is not None and track.id != track_id:
                continue
            for item in track.clips:
                if item.id == clip_id:
                    continue
                candidates.extend([item.timeline_start, item.timeline_start + item.duration])
        nearest = min(candidates, key=lambda value: abs(value - timeline_start))
        return nearest if abs(nearest - timeline_start) <= self.snap_threshold else max(0.0, timeline_start)

    def add_transition(self, left_clip_id: str, right_clip_id: str, kind: str = "fade", duration: float = 0.5) -> Transition:
        left_track, left = self._find(left_clip_id)
        right_track, right = self._find(right_clip_id)
        if left_track.id != right_track.id or left_track.kind != "video":
            raise ValueError("Transitions require two clips on the same video track")
        if right.timeline_start < left.timeline_start:
            left, right = right, left
        if abs((left.timeline_start + left.duration) - right.timeline_start) > 0.05:
            raise ValueError("Transition clips must be adjacent on the timeline")
        if kind not in {"fade"}:
            raise ValueError("Unsupported transition type")
        transition = Transition(new_id(), kind, left_track.id, left.id, right.id, max(0.05, min(duration, left.duration, right.duration)))
        self.project.transitions = [item for item in self.project.transitions if item.left_clip_id != left.id or item.right_clip_id != right.id]
        self.project.transitions.append(transition)
        return transition

    def add_track(self, kind: str, name: str | None = None):
        if kind not in {"video", "audio"}:
            raise ValueError("Track kind must be video or audio")
        count = 1 + sum(1 for track in self.project.tracks if track.kind == kind)
        from findcut.domain.models import Track
        track = Track(new_id(), kind, name or f"{kind.title()} {count}")
        self.project.tracks.append(track)
        return track

    def remove_track(self, track_id: str) -> None:
        if sum(1 for track in self.project.tracks if track.kind == "video") <= 1 and next((track for track in self.project.tracks if track.id == track_id), None) and next(track for track in self.project.tracks if track.id == track_id).kind == "video":
            raise ValueError("A project must keep at least one video track")
        if sum(1 for track in self.project.tracks if track.kind == "audio") <= 1 and next((track for track in self.project.tracks if track.id == track_id), None) and next(track for track in self.project.tracks if track.id == track_id).kind == "audio":
            raise ValueError("A project must keep at least one audio track")
        self.project.tracks = [track for track in self.project.tracks if track.id != track_id]
