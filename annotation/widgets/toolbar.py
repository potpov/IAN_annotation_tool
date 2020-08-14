from PyQt5 import QtCore, QtWidgets
from pyface.qt import QtGui
import qtawesome as qta


class Toolbar(QtGui.QWidget):
    toolbar_save = QtCore.pyqtSignal()
    toolbar_load = QtCore.pyqtSignal()

    def __init__(self):
        super(Toolbar, self).__init__()

        self.bar = QtGui.QToolBar()
        self.bar.setIconSize(QtCore.QSize(32, 32))

        # save
        save_action = QtGui.QAction(qta.icon('fa5s.save'), "Save", self)
        save_action.triggered.connect(self.save)
        save_action.setShortcut("Ctrl+S")
        save_action.setToolTip("Save current state")
        self.bar.addAction(save_action)
        # load
        load_action = QtGui.QAction(qta.icon('fa5s.file-upload'), "Load", self)
        load_action.triggered.connect(self.load)
        load_action.setShortcut("Ctrl+L")
        load_action.setToolTip("Load state")
        self.bar.addAction(load_action)

        self.arch_handler = None

    def save(self):
        self.arch_handler.save_state()
        self.toolbar_save.emit()

    def load(self):
        self.arch_handler.load_state()
        self.toolbar_load.emit()
