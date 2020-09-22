from PyQt5 import QtCore
from pyface.qt import QtGui


class Menu(QtGui.QWidget):
    open = QtCore.pyqtSignal()
    save = QtCore.pyqtSignal()
    autosave = QtCore.pyqtSignal(bool)
    load = QtCore.pyqtSignal()

    def __init__(self, window):
        super(Menu, self).__init__(window)
        self.bar = window.menuBar()

        # menus
        self.file = None
        self.view = None
        self.save_action = None
        self.autosave_action = None
        self.load_action = None

        self.add_menu_file()

    def get(self):
        return self.bar

    def add_menu_file(self):
        self.file = self.bar.addMenu("&File")
        self.add_action_open()
        self.add_action_save()
        self.add_action_autosave()
        self.add_action_load()
        self.enable_save_load(False)
        return self.file

    def add_menu_view(self):
        self.view = self.bar.addMenu("&View")
        return self.view

    def add_action_open(self):
        open_action = QtGui.QAction("&Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open.emit)
        self.file.addAction(open_action)

    def enable_save_load(self, enabled):
        self.save_action.setDisabled(not enabled)
        self.autosave_action.setDisabled(not enabled)
        self.load_action.setDisabled(not enabled)

    def add_action_save(self):
        self.save_action = QtGui.QAction("&Save", self)
        self.save_action.setDisabled(True)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save.emit)
        self.file.addAction(self.save_action)

    def add_action_autosave(self):
        self.autosave_action = QtGui.QAction("Auto-save", self)
        self.autosave_action.setCheckable(True)
        self.autosave_action.setDisabled(True)
        self.autosave_action.triggered.connect(lambda: self.autosave.emit(self.autosave_action.isChecked()))
        self.file.addAction(self.autosave_action)

    def add_action_load(self):
        self.load_action = QtGui.QAction("&Load", self)
        self.load_action.setDisabled(True)
        self.load_action.setShortcut("Ctrl+L")
        self.load_action.triggered.connect(self.load.emit)
        self.file.addAction(self.load_action)

    def add_action_field_view(self, name, func):
        view_action = QtGui.QAction(name, self)
        view_action.triggered.connect(func)
        self.view.addAction(view_action)
