from __future__ import annotations

from pathlib import Path
from typing import Iterable


def transcribe(input_path: str | Path, model_name: str = "turbo", model_root: str | Path | None = None, language: str | None = None) -> list[dict]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("AI captions require the optional faster-whisper package.") from exc
    kwargs = {"device": "cpu", "compute_type": "int8"}
    if model_root:
        kwargs["download_root"] = str(model_root)
    model = WhisperModel(model_name, **kwargs)
    segments, _info = model.transcribe(str(input_path), language=language, vad_filter=True, word_timestamps=True)
    result: list[dict] = []
    for segment in segments:
        words = []
        for word in segment.words or []:
            words.append({"start": float(word.start), "end": float(word.end), "text": word.word.strip()})
        result.append({"start": float(segment.start), "end": float(segment.end), "text": segment.text.strip(), "words": words})
    return result


def write_srt(segments: Iterable[dict], output_path: str | Path) -> Path:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for index, segment in enumerate(segments, start=1):
        lines.extend([str(index), f"{_timestamp(float(segment['start']))} --> {_timestamp(float(segment['end']))}", str(segment['text']).strip(), ""])
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def write_ass(segments: Iterable[dict], output_path: str | Path, title: str = "FindCut Captions") -> Path:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "[Script Info]", f"Title: {title}", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2", "",
        "[V4+ Styles]", "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,Arial,54,&H00FFFFFF,&H0067E8F9,&H90000000,&H70000000,0,0,0,0,100,100,0,0,3,3,1,2,80,80,72,1", "",
        "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for segment in segments:
        words = segment.get("words") or []
        if not words:
            lines.append(f"Dialogue: 0,{_ass_time(float(segment['start']))},{_ass_time(float(segment['end']))},Default,,0,0,0,,{_escape_ass(str(segment['text']).strip())}")
            continue
        for index, word in enumerate(words):
            start = float(word["start"])
            end = float(words[index + 1]["start"]) if index + 1 < len(words) else float(segment["end"])
            before = " ".join(str(item["text"]).strip() for item in words[:index]).strip()
            current = str(word["text"]).strip()
            after = " ".join(str(item["text"]).strip() for item in words[index + 1:]).strip()
            text = " ".join(part for part in [before, r"{\c&H00E8E767&}" + current + r"{\c&H00FFFFFF&}", after] if part)
            lines.append(f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Default,,0,0,0,,{_escape_ass(text)}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def _timestamp(value: float) -> str:
    milliseconds = max(0, int(round(value * 1000)))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def _ass_time(value: float) -> str:
    centiseconds = max(0, int(round(value * 100)))
    hours, remainder = divmod(centiseconds, 360000)
    minutes, remainder = divmod(remainder, 6000)
    seconds, cs = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{cs:02d}"


def _escape_ass(value: str) -> str:
    return value.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}").replace("\n", " ")
