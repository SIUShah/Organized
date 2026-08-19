from __future__ import annotations

from pathlib import Path
import logging

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QPushButton, QSlider, QSplitter, QStatusBar, QToolBar, QVBoxLayout,
    QWidget, QInputDialog, QDialog, QDialogButtonBox, QProgressBar,
)

from findcut.domain.models import Project, TextOverlay, new_id
from findcut.media.ffmpeg import FFmpegAdapter, MediaError
from findcut.media.waveform import WaveformRenderer
from findcut.media.levels import AudioLevelAnalyzer
from findcut.media.analysis import MediaAnalyzer
from findcut.services.export import ExportService
from findcut.services.timeline import TimelineService
from findcut.services.templates import available_templates, create_from_template
from findcut.ai.model_manager import ModelManager
from findcut.ai.transcription import transcribe, write_ass, write_srt

logger = logging.getLogger(__name__)


class FindCutWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FindCut")
        self.resize(1280, 760)
        self.project = Project()
        self.media = FFmpegAdapter()
        self.waveforms = WaveformRenderer(self.media)
        self.levels = AudioLevelAnalyzer(self.media)
        self.analyzer = MediaAnalyzer(self.media)
        self.exporter = ExportService(self.media)
        self.timeline_service = TimelineService(self.project)
        self.project_path: Path | None = None
        self.model_manager = ModelManager()
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self._build_ui()
        self.player.positionChanged.connect(self._player_position_changed)
        self.player.durationChanged.connect(self._player_duration_changed)
        self.player.errorOccurred.connect(lambda *_: self.statusBar().showMessage(f"Preview error: {self.player.errorString()}"))

    def _build_ui(self) -> None:
        self.setStatusBar(QStatusBar(self))
        self._build_menu()
        toolbar = QToolBar("Editing", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        for label, handler in (("Cut", self.cut_selected), ("Split", self.split_selected), ("Text", self.add_text), ("Audio", self.import_media), ("Waveform", self.show_waveform), ("Meters", self.show_audio_levels), ("Undo", self.undo), ("Redo", self.redo)):
            action = QAction(label, self)
            action.triggered.connect(handler)
            toolbar.addAction(action)

        root = QWidget(self)
        root_layout = QVBoxLayout(root)
        top = QSplitter(Qt.Horizontal)
        top.addWidget(self._media_panel())
        top.addWidget(self._preview_panel())
        top.setStretchFactor(1, 1)
        root_layout.addWidget(top, 1)
        root_layout.addWidget(self._timeline_panel())
        self.setCentralWidget(root)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        template_menu = file_menu.addMenu("New from Template")
        for template in available_templates():
            action = QAction(template.name, self)
            action.setToolTip(template.description)
            action.triggered.connect(lambda checked=False, key=template.key: self.new_from_template(key))
            template_menu.addAction(action)
        file_menu.addSeparator()
        for label, handler, shortcut in (("New Project", self.new_project, "Ctrl+N"), ("Open Project…", self.open_project, "Ctrl+O"), ("Save Project", self.save_project, "Ctrl+S"), ("Save Project As…", self.save_project_as, "Ctrl+Shift+S"), ("Export Edited Video…", self.export_project, "Ctrl+E"), ("Export Selected Clip…", self.export_selected_clip, "Ctrl+Shift+E"), ("Extract Audio…", self.extract_audio, "Ctrl+Alt+E")):
            action = QAction(label, self)
            action.setShortcut(shortcut)
            action.triggered.connect(handler)
            file_menu.addAction(action)
        file_menu.addSeparator()
        open_output = QAction("Open Output Folder", self)
        open_output.triggered.connect(self.open_output_folder)
        file_menu.addAction(open_output)
        edit_menu = self.menuBar().addMenu("Edit")
        snap_action = QAction("Snap to clip boundaries", self)
        snap_action.setCheckable(True)
        snap_action.setChecked(True)
        snap_action.triggered.connect(self.toggle_snapping)
        edit_menu.addAction(snap_action)
        add_video_track = QAction("Add Video Track", self)
        add_video_track.triggered.connect(lambda: self.add_track("video"))
        edit_menu.addAction(add_video_track)
        add_audio_track = QAction("Add Audio Track", self)
        add_audio_track.triggered.connect(lambda: self.add_track("audio"))
        edit_menu.addAction(add_audio_track)
        properties = QAction("Clip Properties…", self)
        properties.triggered.connect(self.edit_clip_properties)
        edit_menu.addAction(properties)
        keyframe = QAction("Add Keyframe…", self)
        keyframe.triggered.connect(self.add_keyframe)
        edit_menu.addAction(keyframe)
        fade = QAction("Add Fade Transition to Next Clip", self)
        fade.triggered.connect(self.add_fade_transition)
        edit_menu.addAction(fade)
        silence = QAction("Remove Detected Silence…", self)
        silence.triggered.connect(self.remove_detected_silence)
        edit_menu.addAction(silence)
        scenes = QAction("Detect Scene Changes…", self)
        scenes.triggered.connect(self.detect_scene_changes)
        edit_menu.addAction(scenes)
        file_menu.addSeparator()
        ai_menu = file_menu.addMenu("AI Tools")
        install_model = QAction("Install Whisper Model…", self)
        install_model.triggered.connect(self.install_whisper_model)
        ai_menu.addAction(install_model)
        captions = QAction("Generate Captions (Whisper)…", self)
        captions.triggered.connect(self.generate_captions)
        ai_menu.addAction(captions)
        styled_captions = QAction("Generate Styled Word Captions (ASS)…", self)
        styled_captions.triggered.connect(self.generate_styled_captions)
        ai_menu.addAction(styled_captions)
        file_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

    def _media_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        title = QLabel("MEDIA")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        file_tools = QHBoxLayout()
        add = QPushButton("+ Add Media")
        add.clicked.connect(self.import_media)
        file_tools.addWidget(add)
        add_folder = QPushButton("Add Folder")
        add_folder.clicked.connect(self.import_folder)
        file_tools.addWidget(add_folder)
        layout.addLayout(file_tools)
        tools = QHBoxLayout()
        remove = QPushButton("Remove")
        remove.clicked.connect(self.remove_selected_media)
        tools.addWidget(remove)
        reveal = QPushButton("Open Location")
        reveal.clicked.connect(self.reveal_selected_media)
        tools.addWidget(reveal)
        layout.addLayout(tools)
        self.media_list = QListWidget()
        self.media_list.itemClicked.connect(self.preview_media_item)
        self.media_list.itemDoubleClicked.connect(self.add_selected_to_timeline)
        layout.addWidget(self.media_list)
        return panel

    def _preview_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        title = QLabel("PREVIEW")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(300)
        self.video_widget.setStyleSheet("background:#111827;border-radius:8px;")
        self.player.setVideoOutput(self.video_widget)
        layout.addWidget(self.video_widget, 1)
        controls = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_preview)
        controls.addWidget(self.play_button)
        stop = QPushButton("Stop")
        stop.clicked.connect(self.player.stop)
        controls.addWidget(stop)
        self.position = QSlider(Qt.Horizontal)
        self.position.setRange(0, 0)
        self.position.sliderMoved.connect(self.player.setPosition)
        controls.addWidget(self.position, 1)
        layout.addLayout(controls)
        return panel

    def _timeline_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        title_row = QHBoxLayout()
        title_row.addWidget(QLabel("TIMELINE"))
        title_row.addStretch()
        title_row.addWidget(QLabel("Zoom"))
        zoom = QSlider(Qt.Horizontal)
        zoom.setRange(1, 100)
        zoom.setValue(30)
        zoom.setMaximumWidth(150)
        title_row.addWidget(zoom)
        layout.addLayout(title_row)
        self.timeline = QListWidget()
        self.timeline.setMinimumHeight(160)
        layout.addWidget(self.timeline)
        return panel

    def import_media(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Add Media Files", "", "Media (*.mp4 *.mov *.mkv *.avi *.webm *.mp3 *.wav *.m4a *.png *.jpg *.jpeg);;All files (*)")
        self._import_paths(paths)

    def import_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Add Media Folder")
        if not folder:
            return
        extensions = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".mp3", ".wav", ".m4a", ".png", ".jpg", ".jpeg"}
        paths = [str(path) for path in Path(folder).iterdir() if path.is_file() and path.suffix.lower() in extensions]
        self._import_paths(paths)

    def _import_paths(self, paths: list[str]) -> None:
        for path in paths:
            try:
                probe = self.media.probe(path)
                asset = self.project.add_asset(path, probe.kind, duration=probe.duration, width=probe.width, height=probe.height, fps=probe.fps, sample_rate=probe.sample_rate, channels=probe.channels, metadata=probe.metadata)
                item = QListWidgetItem(f"{Path(path).name}  ·  {probe.kind}  ·  {probe.duration:.1f}s")
                item.setData(Qt.UserRole, asset.id)
                self.media_list.addItem(item)
                self.statusBar().showMessage(f"Imported {Path(path).name}")
            except MediaError as exc:
                QMessageBox.warning(self, "Import failed", str(exc))

    def preview_media_item(self, item: QListWidgetItem) -> None:
        asset = next((a for a in self.project.media if a.id == item.data(Qt.UserRole)), None)
        if asset:
            self.player.setSource(QUrl.fromLocalFile(asset.path))
            self.player.play()
            self.play_button.setText("Pause")

    def toggle_preview(self) -> None:
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_button.setText("Play")
        else:
            self.player.play()
            self.play_button.setText("Pause")

    def _player_position_changed(self, position: int) -> None:
        self.position.blockSignals(True)
        self.position.setValue(position)
        self.position.blockSignals(False)

    def _player_duration_changed(self, duration: int) -> None:
        self.position.setRange(0, max(0, duration))

    def add_selected_to_timeline(self, item: QListWidgetItem) -> None:
        asset_id = item.data(Qt.UserRole)
        asset = next((a for a in self.project.media if a.id == asset_id), None)
        if not asset:
            return
        track = next((t for t in self.project.tracks if t.kind == asset.kind), self.project.tracks[0])
        end = max((c.timeline_start + c.duration for c in track.clips), default=0.0)
        clip = self.project.add_clip(asset.id, track.id, end, 0.0, asset.duration)
        self._refresh_lists()
        self.statusBar().showMessage(f"Added {Path(asset.path).name} to {track.name}")

    def new_from_template(self, key: str) -> None:
        self.project = create_from_template(key)
        self.timeline_service = TimelineService(self.project)
        self.project_path = None
        self.media_list.clear()
        self.timeline.clear()
        self.player.stop()
        self.position.setRange(0, 0)
        self.statusBar().showMessage(f"Created {self.project.name} template")

    def new_project(self) -> None:
        self.project = Project()
        self.timeline_service = TimelineService(self.project)
        self.project_path = None
        self.media_list.clear()
        self.timeline.clear()
        self.player.stop()
        self.position.setRange(0, 0)

    def open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open FindCut Project", "", "FindCut Project (*.findcut)")
        if not path:
            return
        try:
            self.project = Project.load(path)
            self.timeline_service = TimelineService(self.project)
            self.project_path = Path(path)
            self._refresh_lists()
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Open failed", str(exc))

    def save_project(self) -> None:
        if not self.project_path:
            self.save_project_as()
            return
        self.project.save(self.project_path)
        self.statusBar().showMessage("Project saved")

    def save_project_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save FindCut Project", "project.findcut", "FindCut Project (*.findcut)")
        if path:
            self.project_path = Path(path).with_suffix(".findcut")
            self.save_project()

    def export_project(self) -> None:
        if not self.project.media:
            QMessageBox.information(self, "Nothing to export", "Add media to the project first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Edited Video", "findcut-export.mp4", "MP4 Video (*.mp4)")
        if not path:
            return
        try:
            self.exporter.render_project(self.project, path)
            self._show_export_complete(path)
        except (OSError, ValueError, MediaError) as exc:
            logger.exception("Export failed")
            QMessageBox.warning(self, "Export failed", str(exc))

    def export_selected_clip(self) -> None:
        item = self.timeline.currentItem()
        if not item:
            QMessageBox.information(self, "Select a clip", "Select a timeline clip first.")
            return
        try:
            _, clip = self.timeline_service._find(item.data(Qt.UserRole))
            path, _ = QFileDialog.getSaveFileName(self, "Export Selected Clip", "findcut-clip.mp4", "MP4 Video (*.mp4)")
            if path:
                self.exporter.run(self.exporter.make_job(self.project, path, clip))
                self._show_export_complete(path)
        except (OSError, ValueError, MediaError) as exc:
            logger.exception("Clip export failed")
            QMessageBox.warning(self, "Clip export failed", str(exc))

    def extract_audio(self) -> None:
        item = self.timeline.currentItem()
        asset = None
        start = 0.0
        duration = None
        if item:
            try:
                _, clip = self.timeline_service._find(item.data(Qt.UserRole))
                asset = next((a for a in self.project.media if a.id == clip.asset_id), None)
                start, duration = clip.source_in, clip.duration
            except ValueError:
                pass
        if asset is None and self.project.media:
            asset = self.project.media[0]
        if asset is None:
            QMessageBox.information(self, "Nothing to export", "Import media first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Extract Audio", "findcut-audio.m4a", "M4A Audio (*.m4a);;WAV Audio (*.wav)")
        if not path:
            return
        try:
            self.exporter.extract_audio(asset.path, path, start, duration)
            self._show_export_complete(path)
        except (OSError, MediaError) as exc:
            logger.exception("Audio extraction failed")
            QMessageBox.warning(self, "Audio export failed", str(exc))

    def install_whisper_model(self) -> None:
        names = [model.name for model in self.model_manager.available()]
        name, ok = QInputDialog.getItem(self, "Install Whisper Model", "Model:", names, 1, False)
        if not ok:
            return
        try:
            self.statusBar().showMessage(f"Downloading Whisper {name} model…")
            self.model_manager.install(name)
            self.statusBar().showMessage(f"Whisper {name} model is ready")
        except RuntimeError as exc:
            QMessageBox.warning(self, "AI model unavailable", str(exc))

    def generate_captions(self) -> None:
        item = self.media_list.currentItem()
        asset = next((a for a in self.project.media if item and a.id == item.data(Qt.UserRole)), None)
        if asset is None and self.project.media:
            asset = self.project.media[0]
        if asset is None:
            QMessageBox.information(self, "No media", "Import an audio or video file first.")
            return
        names = [model.name for model in self.model_manager.available() if self.model_manager.is_installed(model.name)]
        if not names:
            QMessageBox.information(self, "Install a model", "Choose File → AI Tools → Install Whisper Model first.")
            return
        name, ok = QInputDialog.getItem(self, "Generate Captions", "Installed model:", names, 0, False)
        if not ok:
            return
        output, _ = QFileDialog.getSaveFileName(self, "Save Captions", Path(asset.path).with_suffix(".srt").name, "SubRip captions (*.srt)")
        if not output:
            return
        try:
            segments = transcribe(asset.path, name, self.model_manager.root)
            write_srt(segments, output)
            self._show_export_complete(output)
        except RuntimeError as exc:
            QMessageBox.warning(self, "Caption generation failed", str(exc))

    def generate_styled_captions(self) -> None:
        item = self.media_list.currentItem()
        asset = next((a for a in self.project.media if item and a.id == item.data(Qt.UserRole)), None)
        if asset is None and self.project.media:
            asset = self.project.media[0]
        if asset is None:
            QMessageBox.information(self, "No media", "Import an audio or video file first.")
            return
        names = [model.name for model in self.model_manager.available() if self.model_manager.is_installed(model.name)]
        if not names:
            QMessageBox.information(self, "Install a model", "Choose File → AI Tools → Install Whisper Model first.")
            return
        name, ok = QInputDialog.getItem(self, "Generate Styled Captions", "Installed model:", names, 0, False)
        if not ok:
            return
        output, _ = QFileDialog.getSaveFileName(self, "Save Styled Captions", Path(asset.path).with_suffix(".ass").name, "ASS captions (*.ass)")
        if not output:
            return
        try:
            segments = transcribe(asset.path, name, self.model_manager.root)
            write_ass(segments, output, title=Path(asset.path).stem)
            self._show_export_complete(output)
        except RuntimeError as exc:
            QMessageBox.warning(self, "Caption generation failed", str(exc))

    def _show_export_complete(self, path: str) -> None:
        self.statusBar().showMessage(f"File saved: {path}")
        QMessageBox.information(self, "File saved", f"Saved to:\n{path}")

    def open_output_folder(self) -> None:
        folder = str(self.project_path.parent if self.project_path else Path.home())
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def remove_selected_media(self) -> None:
        item = self.media_list.currentItem()
        if not item:
            self.statusBar().showMessage("Select a media file first.")
            return
        asset_id = item.data(Qt.UserRole)
        self.project.media = [asset for asset in self.project.media if asset.id != asset_id]
        for track in self.project.tracks:
            track.clips = [clip for clip in track.clips if clip.asset_id != asset_id]
        self._refresh_lists()
        self.statusBar().showMessage("Media removed from the project; original file was not changed.")

    def reveal_selected_media(self) -> None:
        item = self.media_list.currentItem()
        if not item:
            self.statusBar().showMessage("Select a media file first.")
            return
        asset = next((a for a in self.project.media if a.id == item.data(Qt.UserRole)), None)
        if asset:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(asset.path).parent)))

    def show_waveform(self) -> None:
        item = self.media_list.currentItem()
        asset = next((candidate for candidate in self.project.media if item and candidate.id == item.data(Qt.UserRole)), None)
        if asset is None:
            timeline_item = self.timeline.currentItem()
            if timeline_item:
                try:
                    _, clip = self.timeline_service._find(timeline_item.data(Qt.UserRole))
                    asset = next((candidate for candidate in self.project.media if candidate.id == clip.asset_id), None)
                except ValueError:
                    asset = None
        if asset is None:
            QMessageBox.information(self, "Waveform", "Select audio or video media first.")
            return
        try:
            output = Path.home() / "FindCut" / "waveforms" / f"{asset.id}.png"
            waveform_path = self.waveforms.render(asset.path, output)
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Waveform — {Path(asset.path).name}")
            dialog.resize(1000, 260)
            layout = QVBoxLayout(dialog)
            image = QLabel()
            image.setAlignment(Qt.AlignCenter)
            image.setPixmap(QPixmap(str(waveform_path)))
            layout.addWidget(image)
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            dialog.exec()
        except MediaError as exc:
            QMessageBox.warning(self, "Waveform failed", str(exc))

    def remove_detected_silence(self) -> None:
        item = self.timeline.currentItem()
        if not item:
            self.statusBar().showMessage("Select an audio or video clip first.")
            return
        try:
            _, clip = self.timeline_service._find(item.data(Qt.UserRole))
            asset = next((candidate for candidate in self.project.media if candidate.id == clip.asset_id), None)
            if asset is None:
                raise ValueError("Media asset not found")
            ranges = self.analyzer.detect_silence(asset.path)
            local_ranges = []
            clip_end = clip.source_out if clip.source_out is not None else clip.source_in + clip.duration * clip.speed
            for silence in ranges:
                start = max(silence.start, clip.source_in)
                end = min(silence.end, clip_end)
                if end > start:
                    local_ranges.append(((start - clip.source_in) / max(clip.speed, 0.001), (end - clip.source_in) / max(clip.speed, 0.001)))
            if not local_ranges:
                QMessageBox.information(self, "Silence removal", "No removable silence was detected inside this clip.")
                return
            answer = QMessageBox.question(self, "Remove silence", f"Detected {len(local_ranges)} silent range(s). Remove them non-destructively?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
            replacement = self.timeline_service.remove_silence(clip.id, local_ranges)
            self._refresh_lists()
            self.statusBar().showMessage(f"Removed silence and created {len(replacement)} retained segment(s)")
        except (ValueError, MediaError) as exc:
            QMessageBox.warning(self, "Silence removal failed", str(exc))

    def detect_scene_changes(self) -> None:
        item = self.media_list.currentItem()
        asset = next((candidate for candidate in self.project.media if item and candidate.id == item.data(Qt.UserRole)), None)
        if asset is None:
            QMessageBox.information(self, "Scene detection", "Select a video in the media bin first.")
            return
        try:
            markers = self.analyzer.detect_scenes(asset.path)
        except MediaError as exc:
            QMessageBox.warning(self, "Scene detection failed", str(exc))
            return
        if not markers:
            QMessageBox.information(self, "Scene detection", "No scene changes exceeded the detection threshold.")
            return
        preview = ", ".join(f"{marker.time:.2f}s" for marker in markers[:20])
        suffix = " …" if len(markers) > 20 else ""
        QMessageBox.information(self, "Scene detection", f"Detected {len(markers)} scene marker(s):\n{preview}{suffix}")
        self.statusBar().showMessage(f"Detected {len(markers)} scene changes")

    def show_audio_levels(self) -> None:
        item = self.media_list.currentItem()
        asset = next((candidate for candidate in self.project.media if item and candidate.id == item.data(Qt.UserRole)), None)
        if asset is None:
            QMessageBox.information(self, "Audio meters", "Select audio or video media first.")
            return
        try:
            measured = self.levels.analyze(asset.path)
        except MediaError as exc:
            QMessageBox.warning(self, "Audio meters failed", str(exc))
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Audio meters — {Path(asset.path).name}")
        dialog.resize(620, 180)
        layout = QVBoxLayout(dialog)
        for label, value in (("Mean", measured.mean_db), ("Peak", measured.peak_db)):
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{label} ({value:.1f} dB)"))
            meter = QProgressBar()
            meter.setRange(0, 60)
            meter.setValue(max(0, min(60, int(round(value + 60)))))
            meter.setFormat("%v / 60 dBFS")
            row.addWidget(meter, 1)
            layout.addLayout(row)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

    def add_text(self) -> None:
        text, ok = QInputDialog.getText(self, "Add text", "Text:")
        if ok and text:
            self.project.text_overlays.append(TextOverlay(new_id(), text, 0.0, 5.0))
            self.statusBar().showMessage("Text overlay added to the project")

    def cut_selected(self) -> None:
        item = self.timeline.currentItem()
        if not item:
            self.statusBar().showMessage("Select a timeline clip first.")
            return
        try:
            self.timeline_service.delete(item.data(Qt.UserRole))
            self._refresh_lists()
            self.statusBar().showMessage("Clip deleted non-destructively")
        except ValueError as exc:
            QMessageBox.warning(self, "Cut failed", str(exc))

    def split_selected(self) -> None:
        item = self.timeline.currentItem()
        if not item:
            self.statusBar().showMessage("Select a timeline clip first.")
            return
        try:
            clip_id = item.data(Qt.UserRole)
            _, clip = self.timeline_service._find(clip_id)
            self.timeline_service.split(clip_id, clip.timeline_start + clip.duration / 2.0)
            self._refresh_lists()
            self.statusBar().showMessage("Clip split at its midpoint")
        except (ValueError, ZeroDivisionError) as exc:
            QMessageBox.warning(self, "Split failed", str(exc))

    def edit_clip_properties(self) -> None:
        item = self.timeline.currentItem()
        if not item:
            self.statusBar().showMessage("Select a timeline clip first.")
            return
        try:
            _, clip = self.timeline_service._find(item.data(Qt.UserRole))
        except ValueError as exc:
            QMessageBox.warning(self, "Clip properties", str(exc))
            return
        transform = clip.transform
        fields = [
            ("Speed", "speed", float(clip.speed)),
            ("Opacity", "opacity", float(transform.get("opacity", clip.opacity))),
            ("Rotation radians", "rotation", float(transform.get("rotation", 0.0))),
            ("Brightness", "brightness", float(transform.get("brightness", 0.0))),
            ("Contrast", "contrast", float(transform.get("contrast", 1.0))),
            ("Saturation", "saturation", float(transform.get("saturation", 1.0))),
        ]
        for label, key, value in fields:
            raw, ok = QInputDialog.getText(self, "Clip Properties", f"{label}:", text=str(value))
            if not ok:
                return
            try:
                parsed = float(raw)
            except ValueError:
                QMessageBox.warning(self, "Clip properties", f"{label} must be numeric.")
                return
            if key == "speed":
                clip.speed = max(0.05, parsed)
            elif key == "opacity":
                clip.opacity = max(0.0, min(1.0, parsed))
                transform[key] = clip.opacity
            else:
                transform[key] = parsed
        self._refresh_lists()
        self.statusBar().showMessage("Clip properties updated")

    def add_keyframe(self) -> None:
        item = self.timeline.currentItem()
        if not item:
            self.statusBar().showMessage("Select a timeline clip first.")
            return
        try:
            _, clip = self.timeline_service._find(item.data(Qt.UserRole))
        except ValueError as exc:
            QMessageBox.warning(self, "Keyframe", str(exc))
            return
        properties = ["opacity", "volume", "brightness", "contrast", "saturation", "rotation", "scale", "x", "y"]
        property_name, ok = QInputDialog.getItem(self, "Add Keyframe", "Property:", properties, 0, False)
        if not ok:
            return
        time_raw, ok = QInputDialog.getText(self, "Add Keyframe", f"Time in clip (0–{clip.duration:.3f}s):", text="0")
        if not ok:
            return
        value_raw, ok = QInputDialog.getText(self, "Add Keyframe", "Value:", text="1.0")
        if not ok:
            return
        try:
            points = self.timeline_service.set_keyframe(clip.id, property_name, float(time_raw), float(value_raw))
        except (ValueError, TypeError) as exc:
            QMessageBox.warning(self, "Keyframe failed", str(exc))
            return
        self._refresh_lists()
        self.statusBar().showMessage(f"{property_name} keyframe added ({len(points)} points)")

    def add_fade_transition(self) -> None:
        item = self.timeline.currentItem()
        if not item:
            self.statusBar().showMessage("Select the first clip in a pair.")
            return
        try:
            track, clip = self.timeline_service._find(item.data(Qt.UserRole))
            following = sorted((candidate for candidate in track.clips if candidate.timeline_start >= clip.timeline_start and candidate.id != clip.id), key=lambda candidate: candidate.timeline_start)
            next_clip = following[0] if following else None
            if next_clip is None:
                raise ValueError("No following clip found on this track")
            duration_raw, ok = QInputDialog.getText(self, "Fade Transition", "Duration (seconds):", text="0.5")
            if not ok:
                return
            transition = self.timeline_service.add_transition(clip.id, next_clip.id, duration=float(duration_raw))
        except (ValueError, TypeError) as exc:
            QMessageBox.warning(self, "Transition failed", str(exc))
            return
        self.statusBar().showMessage(f"Fade transition added: {transition.duration:.2f}s")

    def toggle_snapping(self, enabled: bool) -> None:
        self.timeline_service.snapping_enabled = enabled
        self.statusBar().showMessage("Snapping enabled" if enabled else "Snapping disabled")

    def add_track(self, kind: str) -> None:
        track = self.timeline_service.add_track(kind)
        self._refresh_lists()
        self.statusBar().showMessage(f"Added {track.name}")

    def undo(self) -> None:
        self.statusBar().showMessage("Undo history is reserved for the command stack milestone.")

    def redo(self) -> None:
        self.statusBar().showMessage("Redo history is reserved for the command stack milestone.")

    def _refresh_lists(self) -> None:
        self.media_list.clear()
        self.timeline.clear()
        for asset in self.project.media:
            item = QListWidgetItem(f"{Path(asset.path).name}  ·  {asset.kind}  ·  {asset.duration:.1f}s")
            item.setData(Qt.UserRole, asset.id)
            self.media_list.addItem(item)
        for track in self.project.tracks:
            for clip in track.clips:
                asset = next((a for a in self.project.media if a.id == clip.asset_id), None)
                if asset:
                    keyframe_count = sum(len(points) for points in clip.keyframes.values())
                    animation_marker = f"  |  {keyframe_count} keyframes" if keyframe_count else ""
                    timeline_item = QListWidgetItem(f"{track.name}  |  {Path(asset.path).name}  |  {clip.timeline_start:.1f}s – {clip.timeline_start + clip.duration:.1f}s{animation_marker}")
                    timeline_item.setData(Qt.UserRole, clip.id)
                    self.timeline.addItem(timeline_item)
