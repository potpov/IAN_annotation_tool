from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui

from annotation import WIDGET_MARGIN
from annotation.actions.Action import LeftCanalCpAddedAction, RightCanalCpAddedAction, LeftCanalCpChangedAction, \
    RightCanalCpChangedAction
from annotation.draw import draw_blue_vertical_line
from annotation.spline.spline import Spline
from annotation.utils import numpy2pixmap, clip_range


class CanvasPanorexWidget(QtGui.QWidget):
    spline_changed = QtCore.pyqtSignal()

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
        self.action = None

    def set_img(self):
        self.img = self.arch_handler.panorex
        self.pixmap = numpy2pixmap(self.img)
        self.setFixedSize(self.img.shape[1] + 50, self.img.shape[0] + 50)

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.draw(qp)
        qp.end()

    def draw_single_arch(self, painter, coords, color: QtGui.QColor):
        for point in coords:
            x, y = point
            painter.setPen(color)
            x += WIDGET_MARGIN
            y += WIDGET_MARGIN
            painter.drawPoint(int(x), int(y))

    def draw_spline(self, painter, spline: Spline, color: QtGui.QColor):
        coords = spline.get_spline()
        self.draw_single_arch(painter, coords, color)

        for point in spline.cp:
            x, y = point
            painter.setPen(QtGui.QColor(0, 255, 0))
            color.setAlpha(100)
            painter.setBrush(color)
            rect_x = int((x + WIDGET_MARGIN) - (self.l // 2))
            rect_y = int((y + WIDGET_MARGIN) - (self.l // 2))
            painter.drawRect(rect_x, rect_y, self.l, self.l)

    def draw(self, painter):
        if self.arch_handler is None:
            return
        if self.arch_handler.coords is None:
            return
        painter.drawPixmap(QtCore.QRect(WIDGET_MARGIN, WIDGET_MARGIN, self.pixmap.width(), self.pixmap.height()),
                           self.pixmap)

        self.draw_spline(painter, self.arch_handler.L_canal_spline, QtGui.QColor(255, 0, 0))
        self.draw_spline(painter, self.arch_handler.R_canal_spline, QtGui.QColor(0, 0, 255))

        painter.setPen(QtGui.QColor(0, 0, 255))
        painter.drawLine(WIDGET_MARGIN + self.current_pos, WIDGET_MARGIN,
                         WIDGET_MARGIN + self.current_pos, WIDGET_MARGIN + self.img.shape[0] - 1)

    def check_cp_movement(self, spline, LR, mouse_x, mouse_y):
        for cp_index, (point_x, point_y) in enumerate(spline.cp):
            if abs(point_x - mouse_x) < self.l // 2 and abs(point_y - mouse_y) < self.l // 2:
                drag_x_offset = point_x - mouse_x
                drag_y_offset = point_y - mouse_y
                self.drag_point = (cp_index, LR, (drag_x_offset, drag_y_offset))
                if LR == "L":
                    self.action = LeftCanalCpChangedAction((point_x, point_y), (point_x, point_y), cp_index)
                elif LR == "R":
                    self.action = RightCanalCpChangedAction((point_x, point_y), (point_x, point_y), cp_index)
                else:
                    raise ValueError("Expected spline LR to be either L or R")
                break

    def mousePressEvent(self, QMouseEvent):
        """ Internal mouse-press handler """
        self.drag_point = None
        self.action = None
        mouse_pos = QMouseEvent.pos()
        mouse_x = mouse_pos.x() - WIDGET_MARGIN
        mouse_y = mouse_pos.y() - WIDGET_MARGIN
        if QMouseEvent.button() == QtCore.Qt.LeftButton:
            self.check_cp_movement(self.arch_handler.L_canal_spline, "L", mouse_x, mouse_y)
            self.check_cp_movement(self.arch_handler.R_canal_spline, "R", mouse_x, mouse_y)
        elif QMouseEvent.button() == QtCore.Qt.RightButton:
            self.spline_changed.emit()
            if mouse_x < self.img.shape[1] // 2:
                idx = self.arch_handler.L_canal_spline.add_cp(mouse_x, mouse_y)
                self.arch_handler.history.add(LeftCanalCpAddedAction((mouse_x, mouse_y), idx), debug=True)
            else:
                idx = self.arch_handler.R_canal_spline.add_cp(mouse_x, mouse_y)
                self.arch_handler.history.add(RightCanalCpAddedAction((mouse_x, mouse_y), idx), debug=True)

    def mouseReleaseEvent(self, QMouseEvent):
        """ Internal mouse-release handler """
        self.drag_point = None
        if self.action is not None:
            self.spline_changed.emit()
            self.arch_handler.history.add(self.action, debug=True)
            self.action = None
        self.update()

    def mouseMoveEvent(self, QMouseEvent):
        """ Internal mouse-move handler """
        if self.drag_point is not None:
            self.spline_changed.emit()

            cp_index, LR, (offset_x, offset_y) = self.drag_point
            new_x = QMouseEvent.pos().x() - WIDGET_MARGIN + offset_x
            new_y = QMouseEvent.pos().y() - WIDGET_MARGIN + offset_y

            new_x = clip_range(new_x, 0, self.pixmap.width() - 1)
            new_y = clip_range(new_y, 0, self.pixmap.height() - 1)

            if LR == "L":
                self.action = LeftCanalCpChangedAction((new_x, new_y), self.action.prev, cp_index)
                spline = self.arch_handler.L_canal_spline
            elif LR == "R":
                self.action = RightCanalCpChangedAction((new_x, new_y), self.action.prev, cp_index)
                spline = self.arch_handler.R_canal_spline
            else:
                raise ValueError("Expected spline LR to be either L or R")
            # Set new point data
            new_idx = spline.update_cp(cp_index, new_x, new_y)
            self.drag_point = (new_idx, LR, self.drag_point[2])

            # Redraw curve
            self.update()

    def show_panorex(self, pos=None):
        self.current_pos = pos
        self.set_img()
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
