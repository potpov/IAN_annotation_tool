from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui


class Image(QtGui.QWidget):
    """
    Image with title on top
    """

    def __init__(self, title):
        super(Image, self).__init__()
        self.title = QtWidgets.QLabel(self, text=title)
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        self.img = QtWidgets.QLabel(self)
        self.img.setAlignment(QtCore.Qt.AlignCenter)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.img)

    def setPixmap(self, pixmap):
        self.img.setPixmap(pixmap)

    def update(self):
        self.img.update()
