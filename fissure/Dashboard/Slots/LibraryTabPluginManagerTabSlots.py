#!/usr/bin/env python3
from PyQt5 import QtCore, QtWidgets
import asyncio
import binascii
import os
import qasync
import tempfile
import zipfile

import fissure.comms


def connect_slots(dashboard: QtCore.QObject):
    """Connect Slots for Library Tab Plugin Manager Tab
    
    Parameters
    ----------
    dashboard : QtCore.QObject
        FISSURE dashboard
    """
    # set tool button icons
    style = dashboard.style()
    if style is not None:
        dashboard.ui.toolButton_plugin_pkg_path_manual.setIcon(
            style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirOpenIcon)
        )
        dashboard.ui.toolButton_plugin_pkg_path_auto.setIcon(
            style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_BrowserReload)
        )
        dashboard.ui.toolButton_plugins_upload.setIcon(
            style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ArrowDown)
        )

    dashboard.ui.toolButton_plugin_pkg_path_auto.clicked.connect(
        lambda: _slot_local_plugin_pkg_path_auto(dashboard)
    )

    dashboard.ui.toolButton_plugin_pkg_path_manual.clicked.connect(
        lambda: _slot_local_plugin_pkg_path_manual(dashboard)
    )

    dashboard.ui.textEdit_plugin_pkg_path.textChanged.connect(
        lambda: _slot_plugin_pkg_path_changed(dashboard)
    )

    dashboard.ui.toolButton_plugins_upload.clicked.connect(
        lambda: _slot_plugin_upload(dashboard)
    )

@qasync.asyncSlot(QtCore.QObject)
async def _slot_local_plugin_pkg_path_auto(dashboard: QtCore.QObject):
    """Set Local Plugin Package Path to Default

    Parameters
    ----------
    dashboard : QtCore.QObject
        FISSURE dashboard
    """
    proc = await asyncio.create_subprocess_exec(
        "fissure-plugin-editor", "plugins", "-d",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    output = stdout.decode().strip()
    if "No such file or directory" in output:
        QtCore.QMessageBox.warning(
            dashboard,
            "Plugin Editor Not Found",
            "fissure-plugin-editor is not installed or not found in PATH."
        )
    elif output.startswith("Plugins directory:"):
        plugin_dir = output.split("Plugins directory:")[1].strip()
        dashboard.ui.textEdit_plugin_pkg_path.setText(plugin_dir)

@QtCore.pyqtSlot(QtCore.QObject)
def _slot_local_plugin_pkg_path_manual(dashboard: QtCore.QObject):
    """Set Local Plugin Package Path Manually

    Parameters
    ----------
    dashboard : QtCore.QObject
        FISSURE dashboard
    """
    start_dir = dashboard.ui.textEdit_plugin_pkg_path.text().strip()
    if not start_dir:
        start_dir = QtCore.QDir.homePath()
    # Select a Directory
    dialog = QtWidgets.QFileDialog(dashboard)
    dialog.setWindowTitle("Select Plugin Directory")
    dialog.setDirectory(start_dir)
    dialog.setFileMode(QtWidgets.QFileDialog.Directory)
    dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)

    if dialog.exec_():
        for d in dialog.selectedFiles():
            folder = d
        # Hide Success Label
        dashboard.ui.label2_iq_transfer_folder_success.setVisible(False)

        # Set the text in the text edit
        if folder:
            dashboard.ui.textEdit_plugin_pkg_path.setText(folder)

@qasync.asyncSlot(QtCore.QObject)
async def _slot_plugin_pkg_path_changed(dashboard: QtCore.QObject):
    dir_path = dashboard.ui.textEdit_plugin_pkg_path.text().strip()
    model = QtCore.QStringListModel()
    if QtCore.QDir(dir_path).exists():
        dir_obj = QtCore.QDir(dir_path)
        dir_obj.setFilter(QtCore.QDir.Dirs | QtCore.QDir.NoDotAndDotDot)
        directories = dir_obj.entryList()
        model.setStringList(directories)
    dashboard.ui.listView_plugin_pkgs_local.setModel(model)

@qasync.asyncSlot(QtCore.QObject)
async def _slot_plugin_upload(dashboard: QtCore.QObject):
    """Upload Plugin to Central Hub

    Parameters
    ----------
    dashboard : QtCore.QObject
        FISSURE dashboard
    """
    # check if the plugin directory exists
    plugin_dir = dashboard.ui.textEdit_plugin_pkg_path.text().strip()
    if not plugin_dir:
        QtCore.QMessageBox.warning(
            dashboard,
            "No Plugin Directory",
            "Please set a valid plugin directory."
        )
        return
    
    # get selected plugins
    selected_indexes = dashboard.ui.listView_plugin_pkgs_local.selectedIndexes()
    selected_plugins = [index.data() for index in selected_indexes]

    for plugin in selected_plugins:
        if dashboard.backend.hiprfisr_connected is True:
            plugin_path = os.path.join(plugin_dir, plugin)
            if not os.path.exists(plugin_path):
                QtCore.QMessageBox.warning(
                    dashboard,
                    "Plugin Not Found",
                    f"Plugin directory '{plugin_path}' does not exist."
                )
                continue

            # Create a temporary zip file for the plugin directory
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
                with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(plugin_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, plugin_path)
                            zipf.write(file_path, arcname)
                with open(temp_zip.name, "rb") as f:
                    zip_data = f.read()
                hex_zip_data = binascii.hexlify(zip_data).decode("utf-8").upper()

            PARAMETERS = {
                "plugin_name": plugin,
                "plugin_data": hex_zip_data,
            }
            msg = {
                fissure.comms.MessageFields.IDENTIFIER: fissure.comms.Identifiers.DASHBOARD,
                fissure.comms.MessageFields.MESSAGE_NAME: "savePlugin",
                fissure.comms.MessageFields.PARAMETERS: PARAMETERS,
            }
            await dashboard.backend.hiprfisr_socket.send_msg(
                fissure.comms.MessageTypes.COMMANDS, msg
            )