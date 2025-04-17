import sys
from PyQt5 import QtCore, QtGui, uic, QtWidgets
import os
import subprocess

Ui_MainWindow, QtBaseClass = uic.loadUiType("main.ui")

def get_ubuntu_version():
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("VERSION_ID"):
                    return line.strip().split("=")[1].strip('"')
    except Exception:
        return None

UBUNTU_VERSION = get_ubuntu_version()
USE_SYSTEMCTL = UBUNTU_VERSION and UBUNTU_VERSION >= "24.04"

class MonitorModeTool(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.connect()
        self.refreshInterfaces()

    def connect(self):
        self.pushButton_monitor_mode_execute.clicked.connect(self.monitorMode)
        self.pushButton_managed_mode_execute.clicked.connect(self.managedMode)
        self.pushButton_refresh_interfaces.clicked.connect(self.refreshInterfaces)
        self.pushButton_aircrack.clicked.connect(self.aircrackStartStop)
        self.pushButton_aircrack_file_open.clicked.connect(self.aircrackFileOpen)
        self.pushButton_modprobe.clicked.connect(self.modprobeClicked)

    def stop_network_manager(self):
        cmd = "sudo systemctl stop NetworkManager" if USE_SYSTEMCTL else "sudo service network-manager stop"
        os.system(cmd)
        self.label_terminal.setText(str(self.label_terminal.text()) + f"\n\t{cmd}")

    def start_network_manager(self):
        cmd = "sudo systemctl start NetworkManager" if USE_SYSTEMCTL else "sudo service network-manager start"
        os.system(cmd)
        self.label_terminal.setText(str(self.label_terminal.text()) + f"\n\t{cmd}")

    def refreshInterfaces(self):
        self.label_terminal.setText("Refreshing Interfaces")
        get_interfaces = os.listdir("/sys/class/net/")
        self.comboBox_monitor_mode_interface.clear()
        self.comboBox_managed_mode_interface.clear()
        self.comboBox_aircrack_interface.clear()
        for n in get_interfaces:
            self.comboBox_monitor_mode_interface.addItem(n)
            self.comboBox_managed_mode_interface.addItem(n)
            self.comboBox_aircrack_interface.addItem(n)

        self.comboBox_monitor_mode_interface.setCurrentIndex(self.comboBox_monitor_mode_interface.count()-1)
        self.comboBox_managed_mode_interface.setCurrentIndex(self.comboBox_managed_mode_interface.count()-1)
        self.comboBox_aircrack_interface.setCurrentIndex(self.comboBox_aircrack_interface.count()-1)

        self.label_terminal.setText(self.label_terminal.text() + "\nDone")

    def monitorMode(self):
        self.label_terminal.setText("Starting Monitor Mode")

        get_interface = str(self.comboBox_monitor_mode_interface.currentText())
        get_channel = str(self.comboBox_monitor_mode_channel.currentText())
        get_disable_network_manager = self.checkBox_monitor_mode_disable_network_manager.isChecked()

        if get_disable_network_manager:
            self.stop_network_manager()

        os.system(f"sudo ifconfig {get_interface} down")
        self.label_terminal.setText(self.label_terminal.text() + f"\n\tsudo ifconfig {get_interface} down")
        os.system(f"sudo iwconfig {get_interface} mode monitor")
        self.label_terminal.setText(self.label_terminal.text() + f"\n\tsudo iwconfig {get_interface} mode monitor")
        os.system(f"sudo ifconfig {get_interface} up")
        self.label_terminal.setText(self.label_terminal.text() + f"\n\tsudo ifconfig {get_interface} up")
        os.system(f"sudo iwconfig {get_interface} channel {get_channel}")
        self.label_terminal.setText(self.label_terminal.text() + f"\n\tsudo iwconfig {get_interface} channel {get_channel}")

        self.label_terminal.setText(self.label_terminal.text() + "\nDone")
        proc = subprocess.Popen(f"sudo iwconfig {get_interface} &", shell=True, stdout=subprocess.PIPE)
        output = proc.communicate()[0].decode()
        self.label_terminal.setText(self.label_terminal.text() + "\n\n" + output)

    def managedMode(self):
        self.label_terminal.setText("Starting Managed Mode")
        get_interface = str(self.comboBox_managed_mode_interface.currentText())

        os.system(f"sudo ifconfig {get_interface} down")
        self.label_terminal.setText(self.label_terminal.text() + f"\n\tsudo ifconfig {get_interface} down")
        os.system(f"sudo iwconfig {get_interface} mode managed")
        self.label_terminal.setText(self.label_terminal.text() + f"\n\tsudo iwconfig {get_interface} mode managed")
        os.system(f"sudo ifconfig {get_interface} up")
        self.label_terminal.setText(self.label_terminal.text() + f"\n\tsudo ifconfig {get_interface} up")

        self.start_network_manager()

        self.label_terminal.setText(self.label_terminal.text() + "\nDone")
        proc = subprocess.Popen(f"sudo iwconfig {get_interface} &", shell=True, stdout=subprocess.PIPE)
        output = proc.communicate()[0].decode()
        self.label_terminal.setText(self.label_terminal.text() + "\n\n" + output)

    def aircrackStartStop(self):
        print("Starting Aircrack Capture")
        get_interface = str(self.comboBox_aircrack_interface.currentText())
        get_channel = str(self.comboBox_aircrack_channel.currentText())
        get_mac_filter = str(self.plainTextEdit_aircrack_mac_filter.toPlainText())
        get_filepath = str(self.plainTextEdit_aircrack_filepath.toPlainText())
        os.system(f"sudo airodump-ng -c {get_channel} -d {get_mac_filter} -w {get_filepath} --output-format pcap {get_interface}")
        print("Done")

    def aircrackFileOpen(self):
        print("file open clicked")
        dlg = QtWidgets.QFileDialog()
        dlg.setFileMode(QtWidgets.QFileDialog.AnyFile)
        dlg.setNameFilter("CAP (*.cap)")
        if dlg.exec_():
            filename = dlg.selectedFiles()
            self.plainTextEdit_aircrack_filepath.setPlainText(str(filename[0]) + ".cap")

    def modprobeClicked(self):
        get_driver = str(self.plainTextEdit_driver.toPlainText())
        os.system(f"sudo modprobe {get_driver}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MonitorModeTool()
    window.show()
    sys.exit(app.exec_())
