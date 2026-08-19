# Build on Windows with: pyinstaller --clean findcut_windows.spec
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

findcut_hidden = collect_submodules("findcut")
qt_hidden = collect_submodules("PySide6")
qt_datas = collect_data_files("PySide6")
qt_binaries = collect_dynamic_libs("PySide6")

a = Analysis(
    ["findcut/app/main.py"],
    pathex=["."],
    binaries=qt_binaries,
    datas=qt_datas + [("THIRD_PARTY_LICENSES", "THIRD_PARTY_LICENSES")],
    hiddenimports=findcut_hidden + qt_hidden,
    excludes=[],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FindCut",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="FindCut",
)
