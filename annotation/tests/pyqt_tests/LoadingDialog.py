from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui
import time


class LoadingThread(QtCore.QThread):
    sig = QtCore.pyqtSignal(int)

    def run(self):
        cnt = 0
        while cnt < 100:
            cnt += 1
            time.sleep(0.3)
            self.sig.emit(cnt)


class LoadingDialog(QtGui.QDialog):
    def __init__(self):
        super(LoadingDialog, self).__init__()
        self.layout = QtGui.QVBoxLayout(self)
        self.label = QtWidgets.QLabel("test")
