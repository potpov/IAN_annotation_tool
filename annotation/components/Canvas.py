from PyQt5 import QtCore
from pyface.qt import QtGui
from abc import ABCMeta, abstractmethod
import numpy as np
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

    def draw_poly_approx(self, painter, p, start, end, color, offsetXY=WIDGET_MARGIN):
        if start is None or end is None:
            return
        x_set = list(range(int(start), int(end)))
        y_set = [p(x) for x in x_set]
        points = [(x, y) for x, y in zip(x_set, y_set)]
        self.draw_points(painter, points, color, offsetXY)

    def draw_line_between_points(self, painter, p1, p2, color, offsetXY=WIDGET_MARGIN):
        def get_equidist_points(p1, p2, parts):
            return zip(np.linspace(p1[0], p2[0], parts + 1),
                       np.linspace(p1[1], p2[1], parts + 1))

        P1 = np.array(p1)
        P2 = np.array(p2)
        dist = np.linalg.norm(P2 - P1)
        points = get_equidist_points(P1, P2, int(dist))
        self.draw_points(painter, points, color, offsetXY)

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

        cp_box_color = cp_box_color or spline_color
        painter.setPen(cp_box_color)
        brush = QtGui.QColor(cp_box_color)
        brush.setAlpha(120)
        painter.setBrush(brush)
        for idx, (x, y) in enumerate(spline.cp):
            rect_x = int((x + offsetXY) - (self.l // 2))
            rect_y = int((y + offsetXY) - (self.l // 2))
            painter.drawRect(rect_x, rect_y, self.l, self.l)
            show_cp_idx and painter.drawText(rect_x, rect_y, str(idx))
