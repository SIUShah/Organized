import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from findcut.ui.main_window import FindCutWindow

app = QApplication([])
window = FindCutWindow()
window.show()
QTimer.singleShot(250, app.quit)
raise SystemExit(app.exec())
