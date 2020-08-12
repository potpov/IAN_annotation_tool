from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui

from annotation.draw import draw_blue_vertical_line
from annotation.spline.spline import Spline
from annotation.utils import numpy2pixmap, clip_range


class CanvasPanorexWidget(QtGui.QWidget):
    def __init__(self, parent):
        super(CanvasPanorexWidget, self).__init__()
        self.parent = parent
        self.layout = QtGui.QHBoxLayout(self)
        self.arch_handler = None
        self.l = 8
        self.img = None
        self.pixmap = None
        self.current_pos = 0
        self.drag_point = None

    def set_img(self):
        self.img = self.arch_handler.panorex
        self.pixmap = numpy2pixmap(self.img)
        self.setMinimumWidth(self.img.shape[1] + 50)

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

    def draw_spline(self, painter, spline: Spline, color: QtGui.QColor):
        coords = spline.get_spline()
        self.draw_single_arch(painter, coords, color)

        for point in spline.cp:
            x, y = point
            painter.setPen(QtGui.QColor(0, 255, 0))
            painter.setBrush(QtGui.QColor(0, 255, 0, 100))
            rect_x = int((x + self.x()) - (self.l // 2))
            rect_y = int((y + self.y()) - (self.l // 2))
            painter.drawRect(rect_x, rect_y, self.l, self.l)

    def draw(self, painter):
        if self.arch_handler is None:
            return
        if self.arch_handler.coords is None:
            return
        painter.drawPixmap(QtCore.QRect(self.x(), self.y(), self.pixmap.width(), self.pixmap.height()), self.pixmap)

        self.draw_spline(painter, self.arch_handler.L_canal_spline, QtGui.QColor(255, 0, 0))
        self.draw_spline(painter, self.arch_handler.R_canal_spline, QtGui.QColor(0, 0, 255))

        painter.setPen(QtGui.QColor(0, 0, 255))
        painter.drawLine(self.x() + self.current_pos, self.y(),
                         self.x() + self.current_pos, self.y() + self.img.shape[0] - 1)

    def check_cp_movement(self, spline, name, mouse_x, mouse_y):
        for cp_index, (point_x, point_y) in enumerate(spline.cp):
            if abs(point_x - mouse_x) < self.l // 2:
                if (abs(point_y - mouse_y)) < self.l // 2:
                    drag_x_offset = point_x - mouse_x
                    drag_y_offset = point_y - mouse_y
                    self.drag_point = (cp_index, name, (drag_x_offset, drag_y_offset))
                    break

    def mousePressEvent(self, QMouseEvent):
        """ Internal mouse-press handler """
        self.drag_point = None
        mouse_pos = QMouseEvent.pos()
        mouse_x = mouse_pos.x() - self.x()
        mouse_y = mouse_pos.y() - self.y()
        if QMouseEvent.button() == QtCore.Qt.LeftButton:
            self.check_cp_movement(self.arch_handler.L_canal_spline, "L", mouse_x, mouse_y)
            self.check_cp_movement(self.arch_handler.R_canal_spline, "R", mouse_x, mouse_y)
        elif QMouseEvent.button() == QtCore.Qt.RightButton:
            if mouse_x < self.img.shape[1] // 2:
                self.arch_handler.L_canal_spline.add_cp(mouse_x, mouse_y)
            else:
                self.arch_handler.R_canal_spline.add_cp(mouse_x, mouse_y)

    def mouseReleaseEvent(self, QMouseEvent):
        """ Internal mouse-release handler """
        self.drag_point = None
        # if self.action is not None:
        #     self.arch_handler.history.add(self.action)
        # self.action = None
        # self.spline_changed.emit()
        self.update()

    def mouseMoveEvent(self, QMouseEvent):
        """ Internal mouse-move handler """
        if self.drag_point is not None:
            cp_index, name, (offset_x, offset_y) = self.drag_point
            new_x = QMouseEvent.pos().x() - self.x() + offset_x
            new_y = QMouseEvent.pos().y() - self.y() + offset_y

            new_x = clip_range(new_x, 0, self.pixmap.width() - 1)
            new_y = clip_range(new_y, 0, self.pixmap.height() - 1)

            # self.action = ArchCpChangedAction((new_x, new_y), self.action.prev, cp_index)

            # Set new point data
            if name == "L":
                spline = self.arch_handler.L_canal_spline
            elif name == "R":
                spline = self.arch_handler.R_canal_spline
            else:
                raise ValueError("Expected spline name to be either L or R")
            new_idx = spline.update_cp(cp_index, new_x, new_y)
            self.drag_point = (new_idx, name, self.drag_point[2])

            # Redraw curve
            self.update()

    def show_panorex(self, pos=None):
        self.current_pos = pos
        self.update()


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
        # cv2.imwrite(r"C:\Users\crime\Desktop\alveolar_nerve\dataset\panorex.jpg", panorex * 255)
        self.l_pano.show_panorex(l_panorex, pos)
