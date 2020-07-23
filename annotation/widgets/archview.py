from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui

from annotation.utils import numpy2pixmap, clip_range


class SimpleArchWidget(QtGui.QWidget):

    def __init__(self, parent):
        super(SimpleArchWidget, self).__init__()
        self.parent = parent
        self.layout = QtGui.QHBoxLayout(self)

        self.arch_handler = None

        # arch view
        self.label = QtWidgets.QLabel(self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.label)

    def show_arch(self, arch=True, offsets=True, pos=None):
        pixmap = numpy2pixmap(
            self.arch_handler.get_section(self.arch_handler.selected_slice,
                                          arch=arch,
                                          offsets=offsets,
                                          pos=pos))
        self.label.setPixmap(pixmap)
        self.label.update()


class SplineArchWidget(QtGui.QWidget):
    spline_changed = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(SplineArchWidget, self).__init__()
        self.layout = QtGui.QHBoxLayout(self)
        self.container = parent
        self.arch_handler = None
        self.num_cp = 10
        self.l = 8  # size of the side of the square for the control points
        self.img = None
        self.pixmap = None
        self.current_pos = 0
        self.setMinimumWidth(500)

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.draw(qp)
        qp.end()

    def draw_single_arch(self, painter, coords, color: QtGui.QColor):
        for point in coords:
            x, y = point
            painter.setPen(color)
            x += self.x()
            y += self.y()
            painter.drawPoint(int(x), int(y))

    def draw(self, painter):
        l_offset, coords, h_offset, derivative = self.arch_handler.coords

        painter.drawPixmap(QtCore.QRect(self.x(), self.y(), self.pixmap.width(), self.pixmap.height()), self.pixmap)

        self.draw_single_arch(painter, self.arch_handler.offsetted_arch, QtGui.QColor(0, 255, 255))
        self.draw_single_arch(painter, self.arch_handler.spline.get_spline(), QtGui.QColor(255, 0, 0))
        self.draw_single_arch(painter, l_offset, QtGui.QColor(0, 255, 0))
        self.draw_single_arch(painter, h_offset, QtGui.QColor(0, 255, 0))

        for point in self.arch_handler.spline.cp:
            x, y = point
            painter.setPen(QtGui.QColor(0, 255, 0))
            painter.setBrush(QtGui.QColor(0, 255, 0, 100))
            rect_x = int((x + self.x()) - (self.l // 2))
            rect_y = int((y + self.y()) - (self.l // 2))
            painter.drawRect(rect_x, rect_y, self.l, self.l)

        painter.setPen(QtGui.QColor(0, 0, 255))
        points = self.arch_handler.side_coords[self.current_pos]
        for x, y in points:
            if self.img.shape[1] > x > 0 and self.img.shape[0] > y > 0:
                painter.drawPoint(int(x + self.x()), int(y + self.y()))

    def mousePressEvent(self, QMouseEvent):
        """ Internal mouse-press handler """
        self._drag_point = None
        mouse_pos = QMouseEvent.pos()
        mouse_x = mouse_pos.x() - self.x()
        mouse_y = mouse_pos.y() - self.y()

        for cp_index, (point_x, point_y) in enumerate(self.arch_handler.spline.cp):
            if abs(point_x - mouse_x) < self.l // 2:
                if (abs(point_y - mouse_y)) < self.l // 2:
                    drag_x_offset = point_x - mouse_x
                    drag_y_offset = point_y - mouse_y
                    self._drag_point = (cp_index, (drag_x_offset, drag_y_offset))
                    break

    def mouseReleaseEvent(self, QMouseEvent):
        """ Internal mouse-release handler """
        self._drag_point = None
        self.spline_changed.emit()

    def mouseMoveEvent(self, QMouseEvent):
        """ Internal mouse-move handler """
        if self._drag_point is not None:
            cp_index, (offset_x, offset_y) = self._drag_point
            new_x = QMouseEvent.pos().x() - self.x() + offset_x
            new_y = QMouseEvent.pos().y() - self.y() + offset_y

            new_x = clip_range(new_x, 0, self.pixmap.width() - 1)
            new_y = clip_range(new_y, 0, self.pixmap.height() - 1)

            # Set new point data
            self.arch_handler.spline.set_cp(cp_index, new_x, new_y)

            # Redraw curve
            self.update()

    def show_arch(self, pos=None):
        self.current_pos = pos
        self.update()