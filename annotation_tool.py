from pyface.qt import QtGui
from annotation.screens.Window import Window

if __name__ == "__main__":
    # Don't create a new QApplication, it would unhook the Events
    # set by Traits on the existing QApplication. Simply use the
    # '.instance()' method to retrieve the existing one.
    app = QtGui.QApplication.instance()
    window = Window()
    window.show()
    app.exec_()
