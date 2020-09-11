from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui


class Image(QtGui.QWidget):
    """
    Image with title on top
    """

    def __init__(self, title=""):
        super(Image, self).__init__()
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        if title != "":
            self.title = QtWidgets.QLabel(self, text=title)
            self.title.setAlignment(QtCore.Qt.AlignCenter)
            self.layout.addWidget(self.title)

        self.img = QtWidgets.QLabel(self)
        self.img.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.img)

    def setPixmap(self, pixmap):
        self.img.setPixmap(pixmap)

    def update(self):
        self.img.update()
