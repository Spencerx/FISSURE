# from fissure.Dashboard.Backend import DashboardBackend
from fissure.Dashboard.Frontend import Dashboard
from PyQt5 import QtWidgets, QtCore

import asyncio
import fissure.utils
import qasync
import sys
import os
import atexit

LOCK_FILE = "/tmp/fissure.lock"


def check_existing_instance():
    """ 
    Prevent multiple instances of FISSURE from running. 
    """
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE, "r") as f:
            pid = f.read().strip()
            if pid and os.path.exists(f"/proc/{pid}"):
                print(f"❌ FISSURE is already running (PID: {pid}). Exiting.")
                sys.exit(1)  # Prevent multiple instances

    # Write current process ID to lock file
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))


def cleanup_lock_file():
    """ 
    Remove the lock file when FISSURE exits. 
    """
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


def run():
    """
    Starts FISSURE.
    """
    fissure.utils.init_logging()

    # Check for Certificates Folder
    certificates_directory = os.path.join(fissure.utils.FISSURE_ROOT, "certificates")
    if os.path.exists(certificates_directory):
        pass
        # print("certificates folder found.")
    else:
        print('"certificates" folder not found. Run "Network Certificates" item in installer')
        sys.exit(1)

    # Handle high resolution displays:
    if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    # Set Qt Scaling
    settings = fissure.utils.get_fissure_config()
    qt_scale_factor = settings.get("qt_scale_factor", "1.0") 
    os.environ["QT_SCALE_FACTOR"] = str(qt_scale_factor)  # >=1.0

    # Supress warnings on main menu changing
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.wayland.warning=false"

    app = QtWidgets.QApplication(sys.argv)

    app.setApplicationName("FISSURE")
    app.setDesktopFileName("fissure.desktop")

    eventLoop: asyncio.AbstractEventLoop = qasync.QEventLoop(app)
    asyncio.set_event_loop(eventLoop)

    gui = Dashboard()
    # gui.show()  # Make visible in frontend.py

    with eventLoop:
        eventLoop.run_forever()


if __name__ == "__main__":
    # Prevent multiple instances
    check_existing_instance()
    
    # Ensure lock file is removed on exit
    atexit.register(cleanup_lock_file)


    rc = 0
    # try:
    run()
    # except Exception:
        # rc = 1

    sys.exit(rc)
