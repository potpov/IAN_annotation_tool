from PyQt5 import QtCore, QtWidgets
from pyface.qt import QtGui


class WorkerThread(QtCore.QThread):
    def __init__(self, func):
        super(WorkerThread, self).__init__()
        self.func = func

    def run(self):
        self.func()


class LoadingDialog(QtWidgets.QDialog):
    def __init__(self, func, message="...", parent=None):
        super(LoadingDialog, self).__init__(parent)
        self.setWindowTitle("Wait")
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowTitleHint | QtCore.Qt.CustomizeWindowHint)
        self.layout = QtGui.QVBoxLayout(self)
        self.label = QtWidgets.QLabel(message)
        self.layout.addWidget(self.label)

        self.func = func

        self.thread = WorkerThread(self.func)
        self.thread.finished.connect(self.close)
        self.thread.start()
