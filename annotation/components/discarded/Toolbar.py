from PyQt5 import QtCore
from pyface.qt import QtGui
import qtawesome as qta

from annotation.components.message.Dialog import question


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

        self.arch_handler = ArchHandler()

    def save(self):
        def yes(self):
            self.arch_handler.save_state()
            self.toolbar_save.emit()

        if self.arch_handler.is_there_data_to_load():
            question(self, "Save", "Save data was found. Are you sure you want to overwrite the save?",
                     yes=lambda: yes(self))
        else:
            yes(self)

    def load(self):
        def yes(self):
            self.arch_handler.load_state()
            self.toolbar_load.emit()

        if self.arch_handler.is_there_data_to_load():
            question(self, "Load",
                     "Save data was found. Are you sure you want to discard current changes and load from disk?",
                     yes=lambda: yes(self))
