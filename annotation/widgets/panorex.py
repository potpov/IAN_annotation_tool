from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui

from annotation.draw import draw_blue_vertical_line
from annotation.utils import numpy2pixmap


class SinglePanorexWidget(QtGui.QWidget):
    def __init__(self, parent):
        super(SinglePanorexWidget, self).__init__()
        self.parent = parent

        self.arch_handler = None

        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.pano = QtWidgets.QLabel(self)
        self.pano.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.pano)

    def show_panorex(self, panorex=None, pos=None):
        if panorex is None:
            panorex = self.arch_handler.panorex

        if pos is not None:
            panorex = draw_blue_vertical_line(panorex, pos)

        pixmap = numpy2pixmap(panorex)
        self.pano.setPixmap(pixmap)
        self.pano.update()


class PanorexWidget(QtGui.QWidget):
    def __init__(self, parent):
        super(PanorexWidget, self).__init__()
        self.parent = parent

        self.arch_handler = None

        self.layout = QtGui.QVBoxLayout(self)

        # higher
        self.h_pano = SinglePanorexWidget(self.parent)
        self.layout.addWidget(self.h_pano)

        # main
        self.m_pano = SinglePanorexWidget(self.parent)
        self.layout.addWidget(self.m_pano)

        # lower
        self.l_pano = SinglePanorexWidget(self.parent)
        self.layout.addWidget(self.l_pano)

    def show_panorex(self, pos=None):
        panorex = self.arch_handler.panorex
        l_panorex, h_panorex = self.arch_handler.LHpanorexes

        self.h_pano.show_panorex(h_panorex, pos)
        self.m_pano.show_panorex(panorex, pos)
        self.l_pano.show_panorex(l_panorex, pos)
