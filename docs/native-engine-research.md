# Native editing engine research

## Findings

MLT is an LGPL multimedia framework designed for video editing and currently documents Windows/MSVC compatibility fixes, OpenFX support, hardware scaling, audio transitions, and an `audiowaveform` filter. Its architecture is mature for an editor, but Python integration would likely require bindings or a thin native bridge.

GStreamer Editing Services (GES) is cross-platform, including Windows, and provides timeline, layer, track, clip, effects, project serialization, and pipeline abstractions. It is a strong candidate for an interactive preview engine, but deployment requires shipping the correct GStreamer runtime and plugin set.

libopenshot is explicitly cross-platform and lists multi-layer compositing, effects, animation curves, time mapping, audio mixing/resampling, Qt video playback, Python bindings, unit tests, and FFmpeg codec coverage. It maps closely to FindCut's domain model and is the most direct candidate for a native rendering/preview adapter, subject to verifying current Windows binary packaging and Python binding availability.

## Decision

Keep the tested FFmpeg renderer as the deterministic fallback and export backend. Prototype a `libopenshot` adapter behind a capability-detected interface first, because its documented animation and Python-binding surface most closely matches FindCut's requirements. Evaluate GES as the second option if libopenshot packaging or ABI integration becomes a blocker. MLT remains a valuable third option for advanced filters and transitions, especially where its existing Windows/MSVC work and audio waveform facilities reduce implementation effort.

## References

1. [MLT Framework](https://www.mltframework.org/)
2. [MLT GitHub repository](https://github.com/mltframework/mlt)
3. [GStreamer Editing Services documentation](https://gstreamer.freedesktop.org/documentation/gst-editing-services/index.html)
4. [libopenshot GitHub repository](https://github.com/OpenShot/libopenshot)
