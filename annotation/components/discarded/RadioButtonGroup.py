from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui


class RadioButtonGroup(QtGui.QWidget):
    """
    Unused class
    """
    button_clicked = QtCore.pyqtSignal(str)

    def __init__(self, orientation):
        super(RadioButtonGroup, self).__init__()

        if orientation == QtCore.Qt.Horizontal:
            self.layout = QtGui.QHBoxLayout(self)
        elif orientation == QtCore.Qt.Vertical:
            self.layout = QtGui.QVBoxLayout(self)
        else:
            raise ValueError("Orientation should be either Qt.Horizontal or Qt.Vertical")

        self.buttons = {}
        self.lastClicked = None

    def addButton(self, name):
        button = QtGui.QPushButton(name)
        button.clicked.connect(lambda: self.buttonToggledHandler(name))
        self.buttons[name] = button
        self.layout.addWidget(button)

    def buttonToggledHandler(self, btn):
        self.lastClicked = btn
        self.button_clicked.emit(btn)

    def getLastClicked(self):
        return self.lastClicked
