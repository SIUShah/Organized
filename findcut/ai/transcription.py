from __future__ import annotations

from pathlib import Path
from typing import Iterable


def transcribe(input_path: str | Path, model_name: str = "turbo", model_root: str | Path | None = None, language: str | None = None) -> list[dict[str, float | str]]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("AI captions require the optional faster-whisper package.") from exc
    kwargs = {"device": "cpu", "compute_type": "int8"}
    if model_root:
        kwargs["download_root"] = str(model_root)
    model = WhisperModel(model_name, **kwargs)
    segments, _info = model.transcribe(str(input_path), language=language, vad_filter=True, word_timestamps=True)
    return [{"start": float(segment.start), "end": float(segment.end), "text": segment.text.strip()} for segment in segments]


def write_srt(segments: Iterable[dict[str, float | str]], output_path: str | Path) -> Path:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for index, segment in enumerate(segments, start=1):
        lines.extend([str(index), f"{_timestamp(float(segment['start']))} --> {_timestamp(float(segment['end']))}", str(segment['text']).strip(), ""])
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def _timestamp(value: float) -> str:
    milliseconds = max(0, int(round(value * 1000)))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"
