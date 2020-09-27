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


class ProgressIterator(QtWidgets.QWidget):
    progress_step = QtCore.pyqtSignal(int)

    def __init__(self):
        super(ProgressIterator, self).__init__()
        self.max = 0
        self.val = -1
        self.progress = QtWidgets.QProgressBar()

    def set_max(self, max):
        self.max = max
        self.progress.setMinimum(0)
        self.progress.setMaximum(max)

    def __iter__(self):
        return self

    def __next__(self):
        self.val += 1
        if self.val < self.max:
            self.progress_step.emit(self.val)
            return self.val
        raise StopIteration


class ProgressLoadingDialog(QtWidgets.QDialog):
    progress_s = QtCore.pyqtSignal(int, int)

    def __init__(self, message="Loading", parent=None):
        super(ProgressLoadingDialog, self).__init__(parent)
        self.setWindowTitle(message)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowTitleHint | QtCore.Qt.CustomizeWindowHint)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(300)
        self.iterator = ProgressIterator()
        self.iterator.progress_step.connect(self.set_value)
        self.progress = self.iterator.progress
        self.layout.addWidget(self.progress)
        self.progress_s.connect(self.handle_progress_signal)

    def get_iterator(self, max):
        if self.iterator.max != max:
            self.iterator.set_max(max)
        return self.iterator

    def set_value(self, value):
        self.progress.setValue(value)

    def get_signal(self):
        return lambda val, max: self.progress_s.emit(val, max)

    def handle_progress_signal(self, val, max):
        if self.iterator.max != max:
            self.iterator.set_max(max)
        self.set_value(val)

    def set_function(self, func):
        self.func = func

    def start(self):
        self.thread = WorkerThread(self.func)
        self.thread.finished.connect(self.close)
        self.thread.start()
        self.exec_()


def question(parent, title, message, yes_callback=lambda: None, no_callback=lambda: None,
             default="yes"):
    q = QtGui.QMessageBox()

    defaultButton = q.Yes
    if default.lower() == "no":
        defaultButton = q.No

    r = q.question(parent, title, message, q.Yes | q.No, defaultButton=defaultButton)
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
