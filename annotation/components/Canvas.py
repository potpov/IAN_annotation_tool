from PyQt5 import QtCore
from pyface.qt import QtGui
from abc import ABCMeta, abstractmethod

from annotation import WIDGET_MARGIN


class CanvasMeta(type(QtCore.QObject), ABCMeta):
    pass


class Canvas(QtGui.QWidget, metaclass=CanvasMeta):
    def __init__(self, parent):
        super(Canvas, self).__init__()
        self.layout = QtGui.QHBoxLayout(self)
        self.container = parent
        self.img = None
        self.pixmap = None

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.draw(qp)
        qp.end()

    def draw_background(self, painter, offsetXY=WIDGET_MARGIN):
        if self.pixmap is not None:
            painter.drawPixmap(QtCore.QRect(offsetXY, offsetXY, self.pixmap.width(), self.pixmap.height()), self.pixmap)

    @abstractmethod
    def set_img(self):
        pass

    @abstractmethod
    def draw(self, painter):
        pass

    @abstractmethod
    def show_(self):
        pass


class SplineCanvas(Canvas, metaclass=CanvasMeta):
    def __init__(self, parent):
        super().__init__(parent)
        self.l = 8  # size of the side of the square for the control points
        self.drag_point = None

    @abstractmethod
    def mousePressEvent(self, QMouseEvent):
        pass

    @abstractmethod
    def mouseReleaseEvent(self, QMouseEvent):
        pass

    @abstractmethod
    def mouseMoveEvent(self, QMouseEvent):
        pass

    def draw_points(self, painter, points, color, offsetXY=WIDGET_MARGIN):
        """
        Paints a set of points onto a QPainter.

        Args:
            painter (QtGui.QPainter): where to draw the points
            points (list of (float, float)): list of points to draw
            color (QtGui.QColor): color of the points
            offsetXY (int): offset to apply to each (x, y)
        """
        painter.setPen(color)
        for x, y in points:
            x += offsetXY
            y += offsetXY
            painter.drawPoint(int(x), int(y))

    def draw_spline(self, painter, spline, spline_color, cp_box_color=None, show_cp_idx=False, offsetXY=WIDGET_MARGIN):
        """
        Paints a spline onto a QPainter.

        Args:
            painter (QtGui.QPainter): where to draw the spline
            spline (annotation.spline.spline.Spline): spline to draw
            spline_color (QtGui.QColor): color of the spline
            cp_box_color (QtGui.QColor): color of the control points
            show_cp_idx (bool): draw control point index number
        """
        if spline is None:
            return

        self.draw_points(painter, spline.get_spline(), spline_color, offsetXY)

        for idx, (x, y) in enumerate(spline.cp):
            cp_box_color = cp_box_color or spline_color
            painter.setPen(cp_box_color)
            cp_box_color.setAlpha(100)
            painter.setBrush(cp_box_color)
            rect_x = int((x + offsetXY) - (self.l // 2))
            rect_y = int((y + offsetXY) - (self.l // 2))
            painter.drawRect(rect_x, rect_y, self.l, self.l)
            show_cp_idx and painter.drawText(rect_x, rect_y, str(idx))
