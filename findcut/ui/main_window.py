from __future__ import annotations

from pathlib import Path
import logging

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QPushButton, QSlider, QSplitter, QStatusBar, QToolBar, QVBoxLayout,
    QWidget, QInputDialog,
)

from findcut.domain.models import Project, TextOverlay, new_id
from findcut.media.ffmpeg import FFmpegAdapter, MediaError
from findcut.services.export import ExportService
from findcut.services.timeline import TimelineService

logger = logging.getLogger(__name__)


class FindCutWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FindCut")
        self.resize(1280, 760)
        self.project = Project()
        self.media = FFmpegAdapter()
        self.exporter = ExportService(self.media)
        self.timeline_service = TimelineService(self.project)
        self.project_path: Path | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        self.setStatusBar(QStatusBar(self))
        self._build_menu()
        toolbar = QToolBar("Editing", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        for label, handler in (("Cut", self.cut_selected), ("Split", self.split_selected), ("Text", self.add_text), ("Audio", self.import_media), ("Undo", self.undo), ("Redo", self.redo)):
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
        for label, handler, shortcut in (("New Project", self.new_project, "Ctrl+N"), ("Open Project…", self.open_project, "Ctrl+O"), ("Save Project", self.save_project, "Ctrl+S"), ("Save Project As…", self.save_project_as, "Ctrl+Shift+S"), ("Export Edited Video…", self.export_project, "Ctrl+E"), ("Export Selected Clip…", self.export_selected_clip, "Ctrl+Shift+E"), ("Extract Audio…", self.extract_audio, "Ctrl+Alt+E")):
            action = QAction(label, self)
            action.setShortcut(shortcut)
            action.triggered.connect(handler)
            file_menu.addAction(action)
        file_menu.addSeparator()
        open_output = QAction("Open Output Folder", self)
        open_output.triggered.connect(self.open_output_folder)
        file_menu.addAction(open_output)
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
        self.media_list.itemDoubleClicked.connect(self.add_selected_to_timeline)
        layout.addWidget(self.media_list)
        return panel

    def _preview_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        title = QLabel("PREVIEW")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        self.preview = QLabel("Import media to begin")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(300)
        self.preview.setStyleSheet("background:#111827;color:#94a3b8;border-radius:8px;font-size:18px;")
        layout.addWidget(self.preview, 1)
        controls = QHBoxLayout()
        play = QPushButton("Play")
        play.clicked.connect(lambda: self.statusBar().showMessage("Preview playback is available through the media backend."))
        controls.addWidget(play)
        self.position = QSlider(Qt.Horizontal)
        self.position.setRange(0, 1000)
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

    def new_project(self) -> None:
        self.project = Project()
        self.timeline_service = TimelineService(self.project)
        self.project_path = None
        self.media_list.clear()
        self.timeline.clear()
        self.preview.setText("Import media to begin")

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
                    timeline_item = QListWidgetItem(f"{track.name}  |  {Path(asset.path).name}  |  {clip.timeline_start:.1f}s – {clip.timeline_start + clip.duration:.1f}s")
                    timeline_item.setData(Qt.UserRole, clip.id)
                    self.timeline.addItem(timeline_item)
