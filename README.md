# FindCut

FindCut is an **offline-first, non-destructive multitrack video and audio editor for Windows**, built around PySide6 and FFmpeg with optional AI extensions. Its design goal is professional capability without hiding the execution path: project state is explicit, rendering is testable, and optional native or AI engines are detected rather than silently assumed.

## Verified capabilities

| Area | Implemented behavior | Evidence |
|---|---|---|
| Media workflow | Import individual files or folders, probe metadata, remove assets, reveal source locations, and preview media with Qt Multimedia | `findcut/ui/main_window.py`, `findcut/media/ffmpeg.py` |
| Non-destructive editing | Trim, split, move, delete, snapping, multiple video/audio tracks, project save/open, and recovery backup behavior | `findcut/services/timeline.py`, `findcut/domain/models.py` |
| Rendering | FFmpeg filter-graph compositor with positioned video layers, mixed audio, text overlays, transforms, color controls, speed, opacity, and MP4 export | `findcut/media/renderer.py` |
| Transitions | Validated adjacent-clip fade transitions rendered with timed FFmpeg fade filters | `findcut/services/timeline.py`, `findcut/media/renderer.py` |
| Animation | Persistent clip keyframes with timeline editing controls; opacity and volume render as piecewise-linear frame-evaluated expressions | `findcut/domain/models.py`, `findcut/media/renderer.py` |
| Audio tooling | Waveform PNG generation and mean/peak loudness meters using real FFmpeg analysis | `findcut/media/waveform.py`, `findcut/media/levels.py` |
| AI workflow | Optional Whisper model manager and SRT caption generation; model downloads and licenses remain explicit | `findcut/ai/` |
| Templates | YouTube, vertical Shorts/Reels, podcast-video, and slideshow project defaults | `findcut/services/templates.py` |
| Delivery | GitHub Actions Windows build produces native executable artifacts through PyInstaller | `.github/workflows/windows-build.yml`, `BUILD.md` |

The current repository contains a working, test-backed editor foundation rather than a visual mockup. It is not yet equivalent to DaVinci Resolve: advanced GPU playback, multicam, node compositing, extensive plugin hosting, professional color scopes, and full native-engine integration remain separate engineering milestones.

## Run from source

Install Python 3.11 or newer, install the pinned dependencies, ensure `ffmpeg` and `ffprobe` are available on `PATH`, and run:

```powershell
python -m pip install -r requirements.txt
python -m findcut.app.main
```

The same package can be developed on Linux or macOS when PySide6 and FFmpeg are available. The target distribution is Windows.

## Build the Windows executable

The supported delivery path is GitHub Actions on a Windows runner. The workflow packages the application with PyInstaller and uploads the resulting Windows artifact. Local Windows builds are also documented in [`BUILD.md`](BUILD.md).

```powershell
.\tools\build_windows.ps1
```

Use the latest successful workflow artifact rather than assuming the sandbox itself is a Windows environment. The repository is synchronized at [SIUShah/Organized](https://github.com/SIUShah/Organized).

## Test and evidence

Run the complete test suite with:

```bash
pytest -q
```

The suite covers project persistence, timeline editing, real FFmpeg media probing, multitrack composition, audio mixing, transitions, keyframe management, waveform generation, loudness analysis, Whisper SRT formatting, and optional engine detection. The latest verified local run passed **17 tests**.

## Architecture

The application separates the project domain model, editing services, media adapters, rendering, AI services, and PySide6 presentation layer. The FFmpeg renderer is the deterministic fallback and export path. The optional engine registry detects libopenshot Python bindings and GStreamer/PyGObject without making either a hard dependency.

Native-engine research and the adapter decision are documented in [`docs/native-engine-research.md`](docs/native-engine-research.md). The current recommendation is to prototype libopenshot first because its documented surface includes multi-layer compositing, animation curves, time mapping, audio mixing, Qt playback, Python bindings, and FFmpeg codec coverage. GStreamer Editing Services is the alternative interactive timeline engine, while MLT remains a strong candidate for advanced filters and transitions.

## Optional AI extensions

Whisper transcription is intentionally optional. Users install a model through the model manager and generate SRT captions from the AI Tools menu. Scene analysis, background removal, enhancement, and other model-backed workflows should be added behind the same explicit adapter boundary so model size, compute requirements, and licensing remain visible.

## Licensing

FindCut application code is released under the GNU GPLv3 or later; see [`LICENSE`](LICENSE). Third-party components retain their own licenses. See [`THIRD_PARTY_LICENSES/`](THIRD_PARTY_LICENSES/) and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
