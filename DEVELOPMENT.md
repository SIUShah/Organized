# FindCut Development Guide

FindCut uses a layered Python package. `findcut/domain` owns the non-destructive project schema, `findcut/media` owns FFmpeg integration, `findcut/services` owns application operations, and `findcut/ui` owns PySide6 presentation. Tests in `tests/` must not depend on a visible desktop session.

Run `pytest -q` for automated tests, `python3 -m compileall -q findcut` for syntax checks, and `QT_QPA_PLATFORM=offscreen python3 tools/smoke_ui.py` for a headless UI smoke test on Linux. On Windows, omit the `QT_QPA_PLATFORM` setting and run the smoke script in a desktop session.

The current implementation intentionally keeps native preview/compositing behind service boundaries. Future work should add a proper timeline renderer, audio mixing, waveform generation, playback synchronization, and a command stack without moving media-processing code into widgets.
