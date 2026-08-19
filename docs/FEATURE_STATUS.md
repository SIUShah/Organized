# FindCut Feature Status

## Activated and verified

| Capability | Status | Evidence |
|---|---|---|
| Project creation, templates, save/load | Active | Project model, template service, persistence tests |
| Media import and folder import | Active | PySide6 media panel and FFmpeg probing |
| Multitrack video/audio timeline | Active | Timeline service and project tracks |
| Cut, split, clip deletion, clip properties | Active | Main-window editing actions and tests |
| Speed, opacity, transform, brightness, contrast, saturation | Active | Clip properties and renderer filters |
| Keyframes | Active | Keyframe service and timeline markers |
| Fade transitions | Active | Transition service and renderer support |
| Audio extraction | Active | FFmpeg export service |
| Waveform rendering | Active | Real FFmpeg waveform analysis |
| Audio level analysis | Active | Mean/peak meter dialog |
| Silence detection and non-destructive silence removal | Active | Media analyzer and timeline service |
| Scene-change detection | Active | FFmpeg scene-score analysis |
| Whisper SRT captions | Active when a model is installed | Explicit model manager and transcription workflow |
| Styled word-level ASS captions | Active when a model is installed | ASS caption export action |
| Real FFmpeg project rendering | Active | Timeline renderer and export service |
| Windows packaging workflow | Active | PyInstaller spec and GitHub Actions workflow |
| Undo and redo | **Newly activated** | Bounded project snapshot history, 50 checkpoints, 21 passing tests |
| Media engine status | **Newly activated** | UI dialog reports FFmpeg, libopenshot, and GStreamer availability |

## Partially activated

| Capability | Current state | Limitation |
|---|---|---|
| Native media engines | Registry and Windows build workflow exist | libopenshot/GStreamer are detected or built separately; the shipped editor still uses FFmpeg as its renderer |
| AI tooling | Whisper model management and captions are available | Scene understanding, enhancement, background removal, and object tracking are not integrated into the editor |
| Preview playback | QMediaPlayer preview is available | It is not yet a GPU-optimized timeline compositor with frame-accurate multi-track preview |
| Export presets | YouTube, Shorts/Reels, podcast, and slideshow templates exist | Preset editing, custom preset creation, and one-click platform validation are not complete |
| Timeline navigation | Basic list-based timeline and zoom control exist | A visual track canvas, drag/drop editing, snapping guides, and trim handles are not complete |

## Possible but not yet activated

| Capability | Required work |
|---|---|
| Native libopenshot timeline backend | Complete the Windows native-engine build, create an adapter implementation, and add parity tests against the FFmpeg renderer |
| GPU-accelerated preview and export | Integrate a supported hardware path such as NVENC, AMF, or QSV with capability detection and fallback behavior |
| Drag-and-drop timeline editing | Replace the list timeline with a QGraphicsView/QGraphicsScene editor and command-backed interactions |
| Multicam editing | Add synchronized camera-angle groups, angle switching, and grouped audio handling |
| Advanced color correction | Add color wheels, curves, scopes, LUT import, and GPU-safe filter serialization |
| Chroma key and reliable background removal | Add a dedicated segmentation/matting pipeline with user-editable masks, tracking, and edge refinement |
| Motion/object tracking | Integrate a tracking backend and bind tracks to transforms, masks, and effects |
| Plugin hosting | Define a plugin ABI and sandbox VST3/OFX integration with licensing and crash isolation |
| Proxy media and background conforming | Add proxy generation, relinking, cache management, and background job controls |
| Render queue | Add queued jobs, progress reporting, cancellation, retry, and output validation |
| Advanced title/graphics system | Add keyframeable text styles, lower thirds, templates, and safe-area guides |
| Collaboration and autosave | Add autosave snapshots, recovery, project locking, and conflict-aware project packaging |

## Release assessment

FindCut is a real, test-backed desktop editor foundation with deterministic FFmpeg export. It should be described as an **early professional editor / engineering foundation**, not as a complete DaVinci Resolve replacement. The next highest-value engineering sequence is native backend integration, GPU-aware preview/export, a visual timeline canvas, proxy media, and a render queue.
