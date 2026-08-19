# Mature Media Engine Research

## Findings

MLT is an LGPL multimedia framework designed for video editing and is used by mature editors such as Shotcut and Kdenlive. It provides a strong multitrack/filter/transition model, but integrating its native Windows libraries and Python bindings requires a separately validated build and runtime bundle.

libopenshot is a C++ library with Python bindings and a Qt video player. Its official documentation describes multi-layer compositing, effects, animation curves, time mapping, audio mixing/resampling, frame-rate conversion, unit tests, and broad FFmpeg format support. The official Windows build notes use MSYS2/MinGW and require FFmpeg development libraries, Qt, SWIG, Python, ZeroMQ, and other native dependencies. This is technically the closest match to a Python/PySide6 product layer, but it has the heavier Windows build and redistribution surface.

OpenAI Whisper is MIT-licensed code and model weights with multiple model sizes. The official project requires FFmpeg and downloads model weights separately. `faster-whisper` provides a Python package based on CTranslate2, supports CPU INT8 and GPU modes, and uses PyAV for decoding; it is a good optional transcription adapter but should not be silently bundled into the base Windows package because model files and GPU/runtime dependencies vary substantially.

## Decision

Use a layered integration strategy:

1. Keep the FindCut domain/project model and PySide6 application layer.
2. Keep FFmpeg as the validated fallback for probe, deterministic export, and operations that do not require a live compositor.
3. Add a media-engine adapter boundary for libopenshot first because its documented Python bindings and Qt player align with the current architecture. Build it in a dedicated Windows MSYS2/MinGW workflow and bundle only after runtime tests and license notices pass.
4. Preserve an MLT adapter as the alternative route for multitrack/timeline capabilities if libopenshot’s Windows binding build is not reproducible. Do not ship an untested native engine.
5. Add Whisper/faster-whisper through an optional Model Manager that downloads, verifies, selects, and deletes model weights. Captions are only enabled when a model is present.

## Required validation before claiming maturity

The native engine must pass real tests for multitrack playback, clip seeking, transitions, audio mixing, text/image overlays, effect rendering, project save/reopen, and Windows executable startup. The license register must record version, repository, license, runtime/bundled status, modification status, and redistribution requirements for every native component and model.

## References

[1]: https://github.com/mltframework/mlt "MLT Multimedia Framework"
[2]: https://github.com/openshot/libopenshot "OpenShot Video Library"
[3]: https://openshot.org/files/libopenshot/md__home_gitlab-runner_builds_c8488186_0_OpenShot_libopenshot_doc_INSTALL-WINDOWS.html "libopenshot Windows build instructions"
[4]: https://github.com/openai/whisper "OpenAI Whisper"
[5]: https://pypi.org/project/faster-whisper/ "faster-whisper on PyPI"
