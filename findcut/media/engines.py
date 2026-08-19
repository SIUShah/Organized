from __future__ import annotations

from dataclasses import dataclass
import importlib.util


@dataclass(frozen=True)
class EngineStatus:
    name: str
    available: bool
    reason: str


class MediaEngineRegistry:
    """Detect optional native engines without making them hard dependencies."""

    def statuses(self) -> list[EngineStatus]:
        libopenshot = importlib.util.find_spec("openshot") is not None
        ges = importlib.util.find_spec("gi") is not None
        return [
            EngineStatus("FFmpeg CLI", True, "Deterministic export and fallback renderer"),
            EngineStatus("libopenshot", libopenshot, "Python bindings detected" if libopenshot else "Optional bindings not installed"),
            EngineStatus("GStreamer Editing Services", ges, "PyGObject detected" if ges else "Optional PyGObject/GES runtime not installed"),
        ]

    def preferred(self) -> EngineStatus:
        statuses = self.statuses()
        for status in statuses[1:]:
            if status.available:
                return status
        return statuses[0]
