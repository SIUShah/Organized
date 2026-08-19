# Build on Windows with: pyinstaller findcut_windows.spec
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("findcut")

a = Analysis(
    ["findcut/app/main.py"],
    pathex=["."],
    binaries=[],
    datas=[("THIRD_PARTY_LICENSES", "THIRD_PARTY_LICENSES")],
    hiddenimports=hiddenimports,
    excludes=[],
)

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="FindCut",
    debug=False,
    bootloader_ignore_signals=False,
    console=False,
)
