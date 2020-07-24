from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui

from annotation.utils import numpy2pixmap


class SideVolume(QtGui.QWidget):
    def __init__(self, parent):
        super(SideVolume, self).__init__()
        self.parent = parent

        self.arch_handler = None

        self.layout = QtGui.QVBoxLayout(self)

        self.label = QtWidgets.QLabel(self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.mousePressEvent = self.getPixel
        self.layout.addWidget(self.label)

    def getPixel(self, event):
        x = event.pos().x()
        y = event.pos().y()
        print("x: {} y: {}".format(x, y))

    def show_side_view(self, pos=0):
        try:
            pixmap = numpy2pixmap(self.arch_handler.side_volume[pos])
            self.label.setPixmap(pixmap)
            self.label.update()
        except:
            pass
