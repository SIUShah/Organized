from __future__ import annotations

from pathlib import Path
from typing import Any


class LibOpenShotUnavailable(RuntimeError):
    pass


class LibOpenShotEngine:
    """Optional bridge to libopenshot Python bindings.

    The application remains runnable without the native binding. Once a validated
    libopenshot Windows bundle is staged beside the executable, this adapter is
    the single integration boundary for native readers, writers, and players.
    """

    def __init__(self) -> None:
        try:
            import openshot  # type: ignore
        except ImportError as exc:
            self.module = None
            self.error = exc
        else:
            self.module = openshot
            self.error = None

    @property
    def available(self) -> bool:
        return self.module is not None

    def require(self) -> Any:
        if not self.available:
            raise LibOpenShotUnavailable("libopenshot is not installed in this FindCut runtime.")
        return self.module

    def version(self) -> str:
        module = self.require()
        getter = getattr(module, "get_version", None)
        return str(getter() if getter else getattr(module, "__version__", "unknown"))

    def open_reader(self, path: str | Path) -> Any:
        module = self.require()
        reader = getattr(module, "FFmpegReader", None)
        if reader is None:
            raise LibOpenShotUnavailable("This libopenshot build does not expose FFmpegReader.")
        instance = reader()
        instance.Open(str(path))
        return instance

    def open_writer(self, path: str | Path) -> Any:
        module = self.require()
        writer = getattr(module, "FFmpegWriter", None)
        if writer is None:
            raise LibOpenShotUnavailable("This libopenshot build does not expose FFmpegWriter.")
        return writer(str(path))
