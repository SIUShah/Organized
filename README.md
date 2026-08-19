# FindCut

FindCut is a free, open-source, offline-first Windows video and audio editor designed to hide complexity without hiding capability. The first milestone provides a runnable PySide6 desktop shell, media import and metadata inspection through FFmpeg, a versioned non-destructive project model, basic media-bin-to-timeline placement, text-overlay state, and project save/open.

## Run from source

Install Python 3.11 or newer, install the pinned dependencies, ensure `ffmpeg` and `ffprobe` are on `PATH`, and run:

```bash
python -m pip install -r requirements.txt
python -m findcut.app.main
```

On Windows, the same commands work in PowerShell. A future packaged build will bundle the Python runtime and media binaries so end users do not need Python installed.

## Tests

```bash
pytest -q
```

## Current milestone

The current milestone is the foundation and media workflow. The model already represents multiple tracks, clips, trims, text overlays, image overlays, transitions, and export settings. Timeline playback, non-destructive split commands, full compositing, and rendered export are intentionally isolated for the next implementation milestone rather than represented as fake UI behavior.

## License

FindCut application code is released under the GNU GPLv3 or later; see `LICENSE`. Third-party components retain their own licenses. See `THIRD_PARTY_LICENSES/` and `docs/ARCHITECTURE.md`.
