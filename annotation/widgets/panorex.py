from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui

from annotation.draw import draw_blue_vertical_line
from annotation.utils import numpy2pixmap


class PanorexWidget(QtGui.QWidget):
    def __init__(self, parent):
        super(PanorexWidget, self).__init__()
        self.parent = parent

        self.arch_handler = None

        self.layout = QtGui.QVBoxLayout(self)

        # higher
        self.h_pano = QtWidgets.QLabel(self)
        self.h_pano.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.h_pano)

        # main
        self.m_pano = QtWidgets.QLabel(self)
        self.m_pano.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.m_pano)

        # lower
        self.l_pano = QtWidgets.QLabel(self)
        self.l_pano.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.l_pano)

    def show_panorex(self, pos=None):
        panorex = self.arch_handler.panorex
        l_panorex, h_panorex = self.arch_handler.LHpanorexes
        if pos is not None:
            panorex = draw_blue_vertical_line(panorex, pos)
            l_panorex = draw_blue_vertical_line(l_panorex, pos)
            h_panorex = draw_blue_vertical_line(h_panorex, pos)

        pixmap = numpy2pixmap(panorex)
        self.m_pano.setPixmap(pixmap)
        self.m_pano.update()

        pixmap = numpy2pixmap(l_panorex)
        self.l_pano.setPixmap(pixmap)
        self.l_pano.update()

        pixmap = numpy2pixmap(h_panorex)
        self.h_pano.setPixmap(pixmap)
        self.h_pano.update()
