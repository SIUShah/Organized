from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from findcut.ui.main_window import FindCutWindow


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s", filename="findcut.log")
    app = QApplication(sys.argv)
    app.setApplicationName("FindCut")
    app.setOrganizationName("FindCut Open Source")
    app.setStyleSheet("QMainWindow{background:#f8fafc;} QLabel#sectionTitle{font-weight:700;color:#334155;letter-spacing:1px;} QListWidget{background:white;border:1px solid #cbd5e1;border-radius:6px;padding:4px;} QPushButton{padding:7px 12px;border-radius:5px;background:#2563eb;color:white;} QPushButton:hover{background:#1d4ed8;} QToolBar{spacing:5px;padding:6px;background:#ffffff;border-bottom:1px solid #cbd5e1;}")
    window = FindCutWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
