# FindCut Architecture

## Status

This document records the initial architecture decision for FindCut, a Windows-first, offline desktop editor with a simple interface and a non-destructive project model.

## Foundation decision

FindCut will use **Python with PySide6 for the application layer**, a domain-owned timeline/project model, and an **FFmpeg command-line backend for media inspection and export in the first implementation milestone**. The media backend is isolated behind interfaces so that MLT or libopenshot can be added later for accelerated timeline playback and richer native rendering without coupling the UI to a particular engine.

This choice minimizes initial build risk while preserving a path toward a full native preview engine. MLT is explicitly designed as an LGPL multimedia framework for video editing and has Qt/Python API documentation.[^1] libopenshot offers Python bindings, a Qt video player, compositing, effects, time mapping, and Windows support, but its library is LGPLv3 and its project documentation points commercial redistributors toward additional licensing review.[^2] FFmpeg provides broad format support and a stable process boundary, while its official guidance makes the LGPL/GPL configuration and dynamic-linking obligations explicit.[^3]

FindCut will not fork Shotcut, Kdenlive, or OpenShot’s complete application UI. Their source code remains useful as reference material, but FindCut owns its interface, project schema, command model, and user experience.

## Layered design

```text
PySide6 UI
  ├── MainWindow, media bin, preview, timeline, dialogs
  └── UI actions dispatch domain commands

Application services
  ├── project service
  ├── media import service
  ├── preview service
  └── export service

Domain model
  ├── Project
  ├── MediaAsset
  ├── Timeline / Track / Clip
  ├── TextOverlay / ImageOverlay
  └── ExportSettings

Media adapters
  ├── FFmpeg probe adapter
  ├── FFmpeg export adapter
  └── future MLT/libopenshot preview adapter

Persistence
  └── versioned JSON project files with relative media paths where possible
```

The UI must not call FFmpeg directly. Service objects perform work on worker threads or subprocesses and return typed results or user-safe errors. Detailed diagnostics are written to the application log.

## Project format

A FindCut project uses the `.findcut` extension and contains UTF-8 JSON. The schema is versioned from day one. Media is referenced, never copied into the project by default, and original files are never modified.

The first schema includes project settings, media assets, tracks, clips, overlays, transitions, and export settings. Each clip stores source in/out points and a timeline start, making trim and split operations non-destructive. Future migrations will transform older schema versions before the model is exposed to the UI.

## Threading and failure handling

FFmpeg probes, waveform generation, preview rendering, and export run outside the UI thread. Cancellation is cooperative: FindCut terminates its owned subprocess and reports a controlled failure state. User-facing errors remain concise, for example, “This file could not be opened.” Logs retain the command, return code, and stderr for diagnosis.

## Windows packaging

The target package will be a self-contained Windows x64 directory or installer produced by PyInstaller, with a documented FFmpeg runtime arrangement. The first release will prefer dynamically loaded LGPL-compatible FFmpeg binaries and will ship corresponding source/license notices. H.264/AAC patent and codec distribution considerations are separate from copyright licensing and must be reviewed for the intended distribution jurisdictions before a public release.

## References

[^1]: [MLT Framework GitHub repository](https://github.com/mltframework/mlt)
[^2]: [libopenshot GitHub repository and license](https://github.com/openshot/libopenshot)
[^3]: [FFmpeg License and Legal Considerations](https://www.ffmpeg.org/legal.html)
