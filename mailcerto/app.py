import sys
import asyncio
import os
import platform
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from qasync import QEventLoop
from mailcerto.ui.main_window import MainWindow
from mailcerto.database.models import init_db


def _configure_windows_taskbar():
    """Set AppUserModelID on Windows so Explorer shows the correct application icon
    on the taskbar instead of the Python interpreter icon. This is a no-op on other
    operating systems."""
    if platform.system() != "Windows":
        return
    try:
        import ctypes
        appid = "MailCerto.Application.1.0.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
    except Exception:
        # Non-fatal; the user will still see the icon inside the window chrome.
        pass


def _load_application_icon() -> QIcon:
    """Prefer ICO (Windows) or PNG or SVG, in that order. Always returns a valid
    (possibly empty) QIcon; downstream code checks .isNull()."""
    resources_dir = Path(__file__).resolve().parent / "resources"
    icon = QIcon()

    candidates = [
        resources_dir / "icon.ico",
        resources_dir / "icon.png",
        resources_dir / "icon_256x256.png",
        resources_dir / "icon.svg",
    ]
    for candidate in candidates:
        if candidate.exists():
            candidate_str = str(candidate)
            if icon.isNull():
                icon = QIcon(candidate_str)
            else:
                # Add extra resolutions so Qt picks the most appropriate size
                icon.addFile(candidate_str)
    return icon


def main():
    init_db()

    # On Windows, set the app model ID BEFORE creating the QMainWindow so the
    # taskbar icon is associated with this application, not with python.exe.
    _configure_windows_taskbar()

    app = QApplication(sys.argv)
    app.setApplicationName("MailCerto")
    app.setOrganizationName("MailCerto")
    app.setApplicationDisplayName("MailCerto")
    app.setApplicationVersion("1.0.0")

    # Apply the icon to the application: all top-level windows inherit it.
    app_icon = _load_application_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow(application_icon=app_icon)
    window.show()

    with loop:
        sys.exit(loop.run_forever())


if __name__ == "__main__":
    main()
