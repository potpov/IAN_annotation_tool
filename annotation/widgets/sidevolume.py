from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui

from annotation import WIDGET_MARGIN
from annotation.utils import numpy2pixmap


class CanvasSideVolume(QtGui.QWidget):
    def __init__(self, parent):
        super(CanvasSideVolume, self).__init__()
        self.parent = parent

        self.arch_handler = None
        self.img = None
        self.pixmap = None
        self.drag_point = None
        self.current_pos = 0
        self.r = 5

    def set_img(self):
        self.img = self.arch_handler.side_volume[self.current_pos]
        self.pixmap = numpy2pixmap(self.img)
        self.setFixedSize(self.img.shape[1] + 50, self.img.shape[0] + 50)

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.draw(qp)
        qp.end()

    def draw(self, painter):
        if self.arch_handler is None:
            return
        if self.arch_handler.side_volume is None:
            return

        painter.drawPixmap(
            QtCore.QRect(WIDGET_MARGIN, WIDGET_MARGIN, self.pixmap.width(), self.pixmap.height()),
            self.pixmap)

        z = None
        p, start, end = self.arch_handler.L_canal_spline.get_poly_spline()
        if p is not None and self.current_pos in range(int(start), int(end)):
            z = WIDGET_MARGIN + p(self.current_pos) * self.arch_handler.side_volume_scale
        p, start, end = self.arch_handler.R_canal_spline.get_poly_spline()
        if p is not None and self.current_pos in range(int(start), int(end)):
            z = WIDGET_MARGIN + p(self.current_pos) * self.arch_handler.side_volume_scale

        if z == None:
            return
        painter.setPen(QtGui.QColor(0, 255, 0))
        painter.drawPoint(WIDGET_MARGIN + self.pixmap.width() // 2, z)
        painter.setBrush(QtGui.QColor(0, 255, 0, 100))
        x = WIDGET_MARGIN + self.pixmap.width() // 2
        painter.drawEllipse(QtCore.QPoint(x, z), self.r, self.r)

    def show_side_view(self, pos=0):
        self.current_pos = pos
        self.set_img()
        self.update()


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
