# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for MailCerto.

Produces a single-file Windows GUI executable with icon, version metadata
and bundled resources (templates + icons). Build with:

    pyinstaller MailCerto.spec

Outputs:
    dist\\MailCerto.exe   <- single executable (~60-120 MB)
"""
from __future__ import annotations
import sys
from pathlib import Path

PROJECT_ROOT = Path(SPECPATH).resolve()

ENTRY_POINT = str(PROJECT_ROOT / "mailcerto" / "app.py")
ICON_PATH = str(PROJECT_ROOT / "mailcerto" / "resources" / "icon.ico")

# Resources bundled inside the frozen app. (source, dest_dir_inside_meipass)
datas = [
    (str(PROJECT_ROOT / "mailcerto" / "resources"),  str(Path("mailcerto") / "resources")),
    (str(PROJECT_ROOT / "mailcerto" / "reports" / "templates"),
                                       str(Path("mailcerto") / "reports" / "templates")),
]
if (PROJECT_ROOT / "mailcerto" / "ui" / "themes").exists():
    datas.append((str(PROJECT_ROOT / "mailcerto" / "ui" / "themes"),
                  str(Path("mailcerto") / "ui" / "themes")))


block_cipher = None


a = Analysis(
    [ENTRY_POINT],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # Packages that are dynamically imported or use entry points
        "qtawesome",
        "qtawesome.icon_bundle",
        "qasync",
        "jinja2.ext",
        "dns.dnssec",
        "dns.query",
        "dns.resolver",
        "dns.rdtypes.ANY",
        "cryptography.hazmat.primitives.asymmetric.ec",
        "cryptography.hazmat.primitives.asymmetric.rsa",
        "cryptography.hazmat.primitives.asymmetric.padding",
        "cryptography.hazmat.primitives.hashes",
        "cryptography.hazmat.primitives.serialization",
        "cryptography.x509",
        "cryptography.hazmat.backends",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Save a bit of space: we do not use these Qt modules in the app
        "PySide6.Qt3DCore",
        "PySide6.Qt3DRender",
        "PySide6.Qt3DAnimation",
        "PySide6.Qt3DExtras",
        "PySide6.Qt3DInput",
        "PySide6.Qt3DLogic",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
        "PySide6.QtQuick3D",
        "PySide6.QtQuick",
        "PySide6.QtQuickWidgets",
        "PySide6.QtWebChannel",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebSockets",
        "PySide6.QtPdf",
        "PySide6.QtPdfWidgets",
        "PySide6.QtPositioning",
        "PySide6.QtSensors",
        "PySide6.QtSerialPort",
        "PySide6.QtSql",
        "PySide6.QtTest",
        "PySide6.QtTextToSpeech",
    ],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="MailCerto",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI-only: no console window on Windows
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_PATH if Path(ICON_PATH).exists() else None,
    version=str(PROJECT_ROOT / "scripts" / "version_info.txt"),
)
