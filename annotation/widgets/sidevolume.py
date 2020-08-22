from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui

from annotation import WIDGET_MARGIN
from annotation.components.Canvas import Canvas
from annotation.tests.opencv_tests.test_image_processing import extimate_canal
from annotation.utils import numpy2pixmap


class CanvasSideVolume(Canvas):
    def __init__(self, parent):
        super().__init__(parent)
        self.arch_handler = None
        self.current_pos = 0
        self.r = 3
        self.show_dot = True

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

        if self.show_dot:
            z = None
            LR = None

            # check intersection with L spline
            p, start, end = self.arch_handler.L_canal_spline.get_poly_spline()
            if p is not None and self.current_pos in range(int(start), int(end)):
                LR = "L"
                z = WIDGET_MARGIN + p(self.current_pos) * self.arch_handler.side_volume_scale

            # check intersection with R spline
            p, start, end = self.arch_handler.R_canal_spline.get_poly_spline()
            if p is not None and self.current_pos in range(int(start), int(end)):
                LR = "R"
                z = WIDGET_MARGIN + p(self.current_pos) * self.arch_handler.side_volume_scale

            if z is None:
                return

            x = WIDGET_MARGIN + self.pixmap.width() // 2

            img_canal, hull, mask = extimate_canal(self.img.copy(), (x - WIDGET_MARGIN, z - WIDGET_MARGIN))
            if hull is not None:
                for point in hull:
                    hx, hy = point[0]
                    painter.setPen(QtGui.QColor(200, 121, 219))
                    painter.drawEllipse(QtCore.QPoint(WIDGET_MARGIN + hx, WIDGET_MARGIN + hy), self.r, self.r)

            color = QtGui.QColor(255, 0, 0) if LR == "L" else QtGui.QColor(0, 0, 255)
            painter.setPen(color)
            painter.drawPoint(WIDGET_MARGIN + self.pixmap.width() // 2, z)
            color.setAlpha(100)
            painter.setBrush(color)
            painter.drawEllipse(QtCore.QPoint(x, z), self.r, self.r)

    def show_(self, pos=0, show_dot=False):
        self.show_dot = show_dot
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

    def show_(self, pos=0):
        try:
            pixmap = numpy2pixmap(self.arch_handler.side_volume[pos])
            self.label.setPixmap(pixmap)
            self.label.update()
        except:
            pass
