from PyQt5 import QtWidgets
from pyface.qt import QtGui
import os
from annotation.components.message.Dialog import question
from annotation.components.Menu import Menu
from annotation.screens.Container import Container
from annotation.components.message.Messenger import Messenger
from annotation.components.message.Strategies import QtMessageStrategy


class Window(QtGui.QMainWindow):
    WINDOW_TITLE = "IAN Annotation Tool"
    ICON = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "images", "icon.ico")

    def __init__(self):
        super(Window, self).__init__()

        Messenger(QtMessageStrategy())

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setWindowIcon(QtGui.QIcon(self.ICON))

        self.mb = Menu(self)
        self.mb.open.connect(self.open_dicomdir)
        self.setMenuBar(self.mb.get())

        self.container = Container(self)
        self.setCentralWidget(self.container)

    def open_dicomdir(self):
        dialog = QtWidgets.QFileDialog()
        file_path = dialog.getOpenFileName(None, "Select DICOMDIR file", filter="DICOMDIR")
        path = file_path[0]
        if path:
            self.setWindowTitle("{} - [{}]".format(self.WINDOW_TITLE, path))
            self.container.dicomdir_changed(path)

    def closeEvent(self, event):
        title = "Exit"
        message = "Are you sure you want to quit?"
        question(self, title, message, event.accept, event.ignore, default="No")
