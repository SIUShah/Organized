# Professional Feature Baseline

FindCut will target a focused, usable subset of capabilities found in DaVinci Resolve, Kdenlive, Shotcut, and OpenShot rather than claiming full parity with a large commercial post-production suite.

| Professional area | Reference capability | FindCut implementation target |
|---|---|---|
| Media | Bins, metadata, proxies, source monitoring | Media library, probe metadata, proxy generation, source preview |
| Timeline | Multitrack editing, snapping, 3-point editing, trim tools | Video/audio tracks, playhead, snapping, ripple/overwrite modes, trim/split/move |
| Composition | Layering, transforms, opacity, keyframes | Track-order compositing, crop/scale/rotate/opacity, keyframe curves |
| Color | Primary correction, LUT support, scopes | Brightness/contrast/saturation/hue, LUT loading, histogram/waveform scopes |
| Audio | Multitrack mixing, gain, fades, EQ, compression, waveform | Track mixer, clip gain/volume, fades, waveform display, basic FFmpeg audio filters |
| Text | Titles, captions, subtitles, scrolling/animated text | Text overlays, SRT/ASS import/export, Whisper-generated captions, title templates |
| Effects | Blur, sharpen, chroma key, crop, deinterlace, stylize | Real FFmpeg/MLT/libopenshot filters with parameter persistence |
| Transitions | Dissolve, wipe, slide, fade | Native filter-graph or MLT transitions with overlap semantics |
| AI | Speech-to-text, smart reframing, object/mask workflows | Optional Whisper model manager first; other models only with explicit runtime and license handling |
| Delivery | Presets, render queue, proxy/full-resolution render | YouTube/vertical/podcast presets, queue, progress, deterministic export |

## Integration principle

DaVinci Resolve separates Media, Cut, Edit, Fusion, Color, Fairlight, and Deliver workspaces. Kdenlive documents multitrack editing, proxy editing, keyframeable effects, scopes, subtitles, and online templates. OpenShot documents animated effects and a broad set of video/audio filters. FindCut will use a simpler workspace while preserving the underlying separation between media management, editing, composition, audio, AI, and delivery.

## References

[1]: https://www.blackmagicdesign.com/products/davinciresolve "DaVinci Resolve official product feature page"
[2]: https://kdenlive.org/features/ "Kdenlive official features"
[3]: https://docs.kdenlive.org/en/getting_started/introduction.html "Kdenlive official introduction and capabilities"
[4]: https://www.openshot.org/static/files/user-guide/effects.html "OpenShot official effects documentation"
[5]: https://github.com/mltframework/mlt "MLT Multimedia Framework"
[6]: https://github.com/openshot/libopenshot "OpenShot Video Library"
