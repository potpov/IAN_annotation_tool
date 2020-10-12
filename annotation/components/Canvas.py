from PyQt5 import QtCore
from pyface.qt import QtGui
from abc import abstractmethod
import numpy as np
from annotation.utils.metaclasses import AbstractQObjectMeta
from annotation.utils.margin import WIDGET_MARGIN
import annotation.utils.colors as col


class Canvas(QtGui.QWidget, metaclass=AbstractQObjectMeta):
    MARGIN = 50

    def __init__(self, parent):
        super(Canvas, self).__init__()
        self.layout = QtGui.QHBoxLayout(self)
        self.container = parent
        self.img = None
        self.pixmap = None

    def adjust_size(self):
        if self.img is None:
            return
        self.setFixedSize(self.img.shape[1] + self.MARGIN,
                          self.img.shape[0] + self.MARGIN)

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.draw(qp)
        qp.end()

    def draw_background(self, painter, offsetXY=WIDGET_MARGIN):
        if self.pixmap is not None:
            painter.drawPixmap(QtCore.QRect(offsetXY, offsetXY, self.pixmap.width(), self.pixmap.height()), self.pixmap)

    def draw_poly_approx(self, painter, p, start, end, color, offsetXY=WIDGET_MARGIN):
        if p is None or start is None or end is None:
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

    def draw_arch(self, painter, arch, color, offsetXY=WIDGET_MARGIN):
        """
        Paints an Arch object onto a QPainter.

        Args:
            painter (QtGui.QPainter): where to draw the points
            arch (annotation.core.Arch): Arch object to draw
            color (QtGui.QColor): color of the points
            offsetXY (int): offset to apply to each (x, y)
        """
        self.draw_points(painter, arch.get_arch(), color, offsetXY)

    @abstractmethod
    def set_img(self):
        pass

    @abstractmethod
    def draw(self, painter):
        pass

    @abstractmethod
    def show_(self):
        pass


class SplineCanvas(Canvas, metaclass=AbstractQObjectMeta):
    def __init__(self, parent):
        super().__init__(parent)
        self.l = 8  # size of the side of the square for the control points
        self.drag_point = None
        self._can_edit_spline = True

    def set_can_edit_spline(self, can_edit_spline=None):
        if can_edit_spline is None:
            self._can_edit_spline = not self._can_edit_spline  # changing current state to the opposite
        else:
            self._can_edit_spline = can_edit_spline  # explicitly assign True or False

    @abstractmethod
    def mousePressEvent(self, QMouseEvent):
        pass

    @abstractmethod
    def mouseReleaseEvent(self, QMouseEvent):
        pass

    @abstractmethod
    def mouseMoveEvent(self, QMouseEvent):
        pass

    def draw_spline(self, painter, spline, spline_color, show_cp_boxes=True,
                    cp_box_color=None, show_cp_idx=False, offsetXY=WIDGET_MARGIN):
        """
        Paints a spline onto a QPainter.

        Args:
            painter (QtGui.QPainter): where to draw the spline
            spline (annotation.spline.Spline.Spline): spline to draw
            spline_color (QtGui.QColor): color of the spline
            show_cp_boxes (bool): draw control points or not
            cp_box_color (QtGui.QColor): color of the control points
            show_cp_idx (bool): draw control point index number
        """
        if spline is None:
            return

        self.draw_points(painter, spline.get_spline(), spline_color, offsetXY)

        if show_cp_boxes:
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

    def draw_tilted_plane_line(self, painter, spline, spline_color):
        if spline is None:
            return

        p, start, end = spline.get_poly_spline()
        self.draw_poly_approx(painter, p, start, end, spline_color)
        x = self.current_pos

        if start is not None and end is not None and x in range(int(start), int(end)):
            derivative = np.polyder(p, 1)
            m = -1 / derivative(x)
            y = p(x)
            q = y - m * x
            if q > 10000:
                return
            f = np.poly1d([m, q])
            off = 50
            self.draw_line_between_points(painter, (x - off, f(x - off)),
                                          (x + off, f(x + off)), col.POS)
