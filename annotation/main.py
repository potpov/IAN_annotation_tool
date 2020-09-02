from PyQt5 import QtWidgets
from pyface.qt import QtGui
from annotation.containers.container import Container


class Window(QtGui.QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle("DICOM IAN annotation tool")
        self.menubar = self.menuBar()
        file_menu = self.menubar.addMenu("&File")
        open_action = QtGui.QAction("&Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_dicomdir)
        file_menu.addAction(open_action)
        self.setMenuBar(self.menubar)
        self.container = Container(self)
        self.setCentralWidget(self.container)

    def open_dicomdir(self):
        dialog = QtWidgets.QFileDialog()
        file_path = dialog.getOpenFileName(None, "Select DICOMDIR file", filter="DICOMDIR")
        if file_path[0]:
            self.container.dicomdir_changed.emit(file_path[0])


if __name__ == "__main__":
    # Don't create a new QApplication, it would unhook the Events
    # set by Traits on the existing QApplication. Simply use the
    # '.instance()' method to retrieve the existing one.
    app = QtGui.QApplication.instance()
    window = Window()
    window.show()
    app.exec_()
