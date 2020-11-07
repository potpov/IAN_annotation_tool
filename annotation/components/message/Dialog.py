from PyQt5 import QtCore, QtWidgets
from pyface.qt import QtGui


class WorkerThread(QtCore.QThread):
    def __init__(self, func):
        """
        Thread object that handles a given function that has to be executed without stopping the GUI

        Args:
            func: function that has to be executed
        """
        super(WorkerThread, self).__init__()
        self.func = func

    def run(self):
        self.func()


class LoadingDialog(QtWidgets.QDialog):
    def __init__(self, func, message="Loading", parent=None):
        """
        Dialog window that shows a message while executing a given function in background.

        Its construction implies automatically the execution of the function.

        Args:
            func: function that has to be executed
            message (str): message to show to the user
            parent (pyface.qt.QtGui.QWidget): parent widget
        """
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
        """Iterator widget with a progress bar to monitor the progress"""
        super(ProgressIterator, self).__init__()
        self.max = 0
        self.val = -1
        self.progress = QtWidgets.QProgressBar()

    def set_max(self, max):
        """Sets the maximum of the progress bar"""
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
        """
        Dialog with progress bar

        Args:
            message (str): message to show while executing a function
            parent (pyface.qt.QtGui.QWidget): parent widget
        """
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
        """Sets up the iterator widget and returns it"""
        if self.iterator.max != max:
            self.iterator.set_max(max)
        return self.iterator

    def set_value(self, value):
        """Sets a value in the progress bar"""
        self.progress.setValue(value)

    def get_signal(self):
        """Returns the signal that fills the progress bar"""
        return lambda val, max: self.progress_s.emit(val, max)

    def handle_progress_signal(self, val, max):
        """Handles the emission og the progress signal"""
        if self.iterator.max != max:
            self.iterator.set_max(max)
        self.set_value(val)

    def set_function(self, func):
        self.func = func

    def start(self):
        """Executes the function and shows its progress"""
        self.thread = WorkerThread(self.func)
        self.thread.finished.connect(self.close)
        self.thread.start()
        self.exec_()


def question(parent, title, message, yes=lambda: None, no=lambda: None, default="yes"):
    """
    Shows a question dialog

    Args:
        parent (pyface.qt.QtGui.QWidget): parent widget
        title (str): title of the dialog window
        message (str): message of the dialog window
        yes: function that has to be executed on yes
        no: function that has to be executed on no
        defualt (str): default answer
    """
    q = QtGui.QMessageBox()

    defaultButton = q.Yes
    if default.lower() == "no":
        defaultButton = q.No

    r = q.question(parent, title, message, q.Yes | q.No, defaultButton=defaultButton)
    if r == q.Yes:
        yes()
    else:
        no()


def warning(parent, title, message):
    """
    Shows a warning dialog

    Args:
        parent (pyface.qt.QtGui.QWidget): parent widget
        title (str): title of the dialog window
        message (str): message of the dialog window
    """
    w = QtGui.QMessageBox()
    w.warning(parent, title, message)


def information(parent, title, message):
    """
    Shows an information dialog

    Args:
        parent (pyface.qt.QtGui.QWidget): parent widget
        title (str): title of the dialog window
        message (str): message of the dialog window
    """
    q = QtGui.QMessageBox()
    q.information(parent, title, message)
