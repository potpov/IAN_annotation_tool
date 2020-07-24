from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui


class PrevNextButtons(QtGui.QWidget):
    prev_clicked = QtCore.pyqtSignal()
    next_clicked = QtCore.pyqtSignal()

    def __init__(self):
        """ Wrapper around two buttons: "prev" and "next" """
        super(PrevNextButtons, self).__init__()
        self.prev_btn = QtWidgets.QPushButton("Prev")
        self.prev_btn.clicked.connect(self.prev_clicked.emit)
        self.next_btn = QtWidgets.QPushButton("Next")
        self.next_btn.clicked.connect(self.next_clicked.emit)
        self.layout = QtGui.QHBoxLayout(self)
        self.layout.addWidget(self.prev_btn)
        self.layout.addWidget(self.next_btn)
