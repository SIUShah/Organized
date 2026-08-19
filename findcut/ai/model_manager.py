from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil


@dataclass(frozen=True)
class ModelInfo:
    name: str
    label: str
    approximate_size: str


WHISPER_MODELS = (
    ModelInfo("tiny", "Whisper Tiny", "~1 GB RAM"),
    ModelInfo("base", "Whisper Base", "~1 GB RAM"),
    ModelInfo("small", "Whisper Small", "~2 GB RAM"),
    ModelInfo("medium", "Whisper Medium", "~5 GB RAM"),
    ModelInfo("large-v3", "Whisper Large v3", "~10 GB RAM"),
    ModelInfo("turbo", "Whisper Turbo", "~6 GB RAM"),
)


class ModelManager:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or (Path.home() / ".findcut" / "models"))
        self.root.mkdir(parents=True, exist_ok=True)

    def available(self) -> tuple[ModelInfo, ...]:
        return WHISPER_MODELS

    def path_for(self, name: str) -> Path:
        if name not in {model.name for model in WHISPER_MODELS}:
            raise ValueError(f"Unsupported Whisper model: {name}")
        return self.root / name

    def is_installed(self, name: str) -> bool:
        path = self.path_for(name)
        return path.exists() and any(path.iterdir())

    def install(self, name: str) -> Path:
        """Download model files through faster-whisper's verified model loader."""
        target = self.path_for(name)
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("AI captions require the optional faster-whisper package.") from exc
        WhisperModel(name, device="cpu", compute_type="int8", download_root=str(self.root))
        return target

    def delete(self, name: str) -> None:
        path = self.path_for(name)
        if path.exists():
            shutil.rmtree(path)
