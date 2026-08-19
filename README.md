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

The current milestone is a usable editing and composition workflow. FindCut supports multi-file video/audio/image import, folder import, media removal and location opening, non-destructive timeline clips, trim/split/delete/move operations, project recovery backups, multi-clip FFmpeg timeline composition, edited MP4 export, selected-clip export, and audio extraction. Advanced synchronized preview playback, keyframe animation, richer transitions, and a full caption compositor remain roadmap work.

## License

FindCut application code is released under the GNU GPLv3 or later; see `LICENSE`. Third-party components retain their own licenses. See `THIRD_PARTY_LICENSES/` and `docs/ARCHITECTURE.md`.

## Real playback and templates

The desktop preview uses Qt Multimedia with the bundled FFmpeg-enabled Qt runtime on supported platforms. The File menu includes project templates for YouTube 1080p, vertical Shorts/Reels, podcast video, and photo slideshow workflows. Templates configure the project canvas and export defaults; users still add their own source media.

FindCut’s current renderer is a tested FFmpeg filter pipeline with a Qt playback surface. The architecture keeps the media boundary isolated so a future Windows bundle can replace or augment it with MLT or libopenshot when the native libraries and redistribution notices are validated. The project does not pretend that a Python-only shell is equivalent to a mature editor until those playback, effect, and timeline paths are tested end to end.

## Optional AI extensions

Speech-to-text captions, scene detection, background removal, and enhancement models are intentionally optional extensions rather than hidden dependencies. They require model downloads, additional CPU/GPU resources, and separate model licenses. The planned AI adapter boundary keeps those features replaceable and prevents a large pretrained model from silently being redistributed without its license and size requirements being documented.
