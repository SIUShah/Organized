from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import json
import uuid

SCHEMA_VERSION = 1


def new_id() -> str:
    return uuid.uuid4().hex


@dataclass
class MediaAsset:
    id: str
    path: str
    kind: str
    duration: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    sample_rate: int = 0
    channels: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Clip:
    id: str
    asset_id: str
    track_id: str
    timeline_start: float = 0.0
    source_in: float = 0.0
    source_out: float | None = None
    volume: float = 1.0
    muted: bool = False
    speed: float = 1.0
    opacity: float = 1.0
    transform: dict[str, float] = field(default_factory=dict)
    keyframes: dict[str, list[tuple[float, float]]] = field(default_factory=dict)

    @property
    def duration(self) -> float:
        if self.source_out is None:
            return 0.0
        return max(0.0, (self.source_out - self.source_in) / max(self.speed, 0.001))


@dataclass
class Track:
    id: str
    kind: str
    name: str
    clips: list[Clip] = field(default_factory=list)
    muted: bool = False


@dataclass
class TextOverlay:
    id: str
    text: str
    start: float
    duration: float
    x: float = 0.5
    y: float = 0.5
    font_family: str = "Arial"
    font_size: int = 48
    color: str = "#ffffff"


@dataclass
class ImageOverlay:
    id: str
    path: str
    start: float
    duration: float
    x: float = 0.5
    y: float = 0.5
    scale: float = 1.0
    opacity: float = 1.0
    rotation: float = 0.0


@dataclass
class Transition:
    id: str
    kind: str
    track_id: str
    left_clip_id: str
    right_clip_id: str
    duration: float = 0.5


@dataclass
class ExportSettings:
    format: str = "mp4"
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    width: int = 1920
    height: int = 1080
    fps: float = 30.0
    video_bitrate: str = "8M"
    audio_bitrate: str = "192k"


@dataclass
class Project:
    name: str = "Untitled Project"
    settings: dict[str, Any] = field(default_factory=lambda: {"width": 1920, "height": 1080, "fps": 30.0})
    media: list[MediaAsset] = field(default_factory=list)
    tracks: list[Track] = field(default_factory=lambda: [Track(new_id(), "video", "Video 1"), Track(new_id(), "audio", "Audio 1")])
    text_overlays: list[TextOverlay] = field(default_factory=list)
    image_overlays: list[ImageOverlay] = field(default_factory=list)
    transitions: list[Transition] = field(default_factory=list)
    export: ExportSettings = field(default_factory=ExportSettings)

    def add_asset(self, path: str, kind: str = "unknown", **metadata: Any) -> MediaAsset:
        asset = MediaAsset(id=new_id(), path=str(Path(path)), kind=kind, metadata=metadata)
        for key in ("duration", "width", "height", "fps", "sample_rate", "channels"):
            if key in metadata:
                setattr(asset, key, metadata[key])
        self.media.append(asset)
        return asset

    def add_clip(self, asset_id: str, track_id: str, start: float = 0.0, source_in: float = 0.0, source_out: float | None = None) -> Clip:
        clip = Clip(new_id(), asset_id, track_id, start, source_in, source_out)
        for track in self.tracks:
            if track.id == track_id:
                track.clips.append(clip)
                track.clips.sort(key=lambda item: item.timeline_start)
                return clip
        raise ValueError(f"Track not found: {track_id}")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["schema_version"] = SCHEMA_VERSION
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Project:
        version = payload.get("schema_version", 1)
        if version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported project schema version: {version}")
        tracks: list[Track] = []
        for raw_track in payload.get("tracks", []):
            clips = [Clip(**raw_clip) for raw_clip in raw_track.get("clips", [])]
            tracks.append(Track(id=raw_track["id"], kind=raw_track["kind"], name=raw_track["name"], clips=clips, muted=raw_track.get("muted", False)))
        if not tracks:
            tracks = [Track(new_id(), "video", "Video 1"), Track(new_id(), "audio", "Audio 1")]
        return cls(
            name=payload.get("name", "Untitled Project"),
            settings=payload.get("settings", {}),
            media=[MediaAsset(**item) for item in payload.get("media", [])],
            tracks=tracks,
            text_overlays=[TextOverlay(**item) for item in payload.get("text_overlays", [])],
            image_overlays=[ImageOverlay(**item) for item in payload.get("image_overlays", [])],
            transitions=[Transition(**item) for item in payload.get("transitions", [])],
            export=ExportSettings(**payload.get("export", {})),
        )

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self.to_dict(), indent=2)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(payload, encoding="utf-8")
        if target.exists():
            backup = target.with_suffix(target.suffix + ".bak")
            backup.write_bytes(target.read_bytes())
        temporary.replace(target)

    @classmethod
    def load(cls, path: str | Path) -> Project:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
