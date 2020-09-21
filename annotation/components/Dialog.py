from PyQt5 import QtCore, QtWidgets
from pyface.qt import QtGui


class WorkerThread(QtCore.QThread):
    def __init__(self, func):
        super(WorkerThread, self).__init__()
        self.func = func

    def run(self):
        self.func()


class LoadingDialog(QtWidgets.QDialog):
    def __init__(self, func, message="Loading", parent=None):
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
        self.exec_()


class MessageDialog(QtWidgets.QDialog):
    """TEST CLASS"""

    def __init__(self, title, message, parent=None):
        super(MessageDialog, self).__init__(parent)

        self.title = title
        self.message = message

        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(title)

        self.label = QtWidgets.QLabel(message)
        self.ok = QtWidgets.QPushButton("Ok")
        self.ok.clicked.connect(self.close)

        self.setMinimumSize(300, 200)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.ok)

        self.thread = WorkerThread()
        self.thread.finished.connect(self.close)
        self.thread.start()


def question(parent, title, message, yes_callback=lambda: None, no_callback=lambda: None):
    q = QtGui.QMessageBox()
    r = q.question(parent, title, message, q.Yes | q.No)
    if r == q.Yes:
        yes_callback()
    else:
        no_callback()


def warning(parent, title, message):
    w = QtGui.QMessageBox()
    w.warning(parent, title, message)


def information(parent, title, message):
    q = QtGui.QMessageBox()
    q.information(parent, title, message)


def show_message_box(kind, title, message, yes_callback=None, no_callback=None, details="", parent=None):
    # FIXME: if I create a messagebox like this, closing it will make the application crash if Windows sound is still active.
    return
    ##########
    kind = kind.capitalize()
    if kind not in ['Information', 'Question', 'Warning', 'Critical']:
        kind = 'Information'
    msg = QtWidgets.QMessageBox(parent=parent)
    msg.setIcon(getattr(QtWidgets.QMessageBox, kind))
    msg.setWindowTitle(title)
    msg.setText(message)
    if details != "":
        msg.setDetailedText(details)
    if yes_callback is not None or no_callback is not None:
        msg.setStandardButtons(msg.Yes | msg.No)
    ret = msg.exec()
    if ret == msg.Yes:
        if yes_callback is not None:
            yes_callback()
    elif ret == msg.No:
        if no_callback is not None:
            no_callback()
