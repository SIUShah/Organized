# Building FindCut on Windows

## Development build

Install Python 3.11+, Git, and an FFmpeg build containing `ffmpeg.exe` and `ffprobe.exe`. Create a virtual environment, install `requirements.txt`, and run the application with `python -m findcut.app.main`.

## Test build

Run `pytest -q`. The tests generate a one-second synthetic MP4 with FFmpeg, probe it, and exercise project serialization and timeline data operations.

## Packaging plan

The release package will use PyInstaller in `--onedir` mode. The package must include the PySide6 runtime, FindCut modules, FFmpeg/FFprobe binaries, their corresponding license notices, and a `THIRD_PARTY_LICENSES` directory. The release process must record the exact FFmpeg build, configuration flags, and source URL. FFmpeg’s official LGPL checklist recommends dynamic linking on Windows and distributing the exact corresponding source, while GPL or nonfree components change the licensing analysis; see the project’s legal page before each release.

A signed installer can be added after the first end-to-end rendered export milestone. Until then, the directory package is the more transparent engineering artifact for testing.
