from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui

from annotation.utils.margin import WIDGET_MARGIN
import annotation.utils.colors as col
from annotation.actions.Action import (
    LeftCanalCpAddedAction,
    RightCanalCpAddedAction,
    LeftCanalCpChangedAction,
    RightCanalCpChangedAction,
    LeftCanalCpRemovedAction,
    RightCanalCpRemovedAction
)
from annotation.components.Canvas import SplineCanvas
from annotation.utils.image import draw_blue_vertical_line
from annotation.utils.qt import numpy2pixmap
from annotation.utils.math import clip_range
from annotation.core.ArchHandler import ArchHandler


class CanvasPanorexWidget(SplineCanvas):
    spline_changed = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.current_pos = None
        self.arch_handler = ArchHandler()
        self.action = None

    def set_img(self):
        self.img = self.arch_handler.get_panorex()
        self.pixmap = numpy2pixmap(self.img)
        self.adjust_size()

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.draw(qp)
        qp.end()

    def draw(self, painter):
        if self.arch_handler is None:
            return
        if self.arch_handler.coords is None:
            return

        self.draw_background(painter)

        if self.current_pos is not None:
            painter.setPen(col.POS)
            painter.drawLine(WIDGET_MARGIN + self.current_pos, WIDGET_MARGIN,
                             WIDGET_MARGIN + self.current_pos, WIDGET_MARGIN + self.img.shape[0] - 1)

        if not self.arch_handler.tilted():
            self.draw_spline(painter, self.arch_handler.L_canal_spline, col.L_CANAL_SPLINE)
            self.draw_spline(painter, self.arch_handler.R_canal_spline, col.R_CANAL_SPLINE)
        else:
            self.draw_tilted_plane_line(painter, self.arch_handler.L_canal_spline, col.L_CANAL_SPLINE)
            self.draw_tilted_plane_line(painter, self.arch_handler.R_canal_spline, col.R_CANAL_SPLINE)

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

    def cp_clicked(self, spline, mouse_x, mouse_y):
        for cp_index, (point_x, point_y) in enumerate(spline.cp):
            if abs(point_x - mouse_x) < self.l // 2 and abs(point_y - mouse_y) < self.l // 2:
                return cp_index
        return None

    def handle_right_click(self, mouse_x, mouse_y):
        remove_L = self.cp_clicked(self.arch_handler.L_canal_spline, mouse_x, mouse_y)
        remove_R = self.cp_clicked(self.arch_handler.R_canal_spline, mouse_x, mouse_y)
        if remove_L is not None:
            self.arch_handler.L_canal_spline.remove_cp(remove_L)
            self.arch_handler.history.add(LeftCanalCpRemovedAction(remove_L))
        elif remove_R is not None:
            self.arch_handler.R_canal_spline.remove_cp(remove_R)
            self.arch_handler.history.add(RightCanalCpRemovedAction(remove_R))

        else:
            if mouse_x < self.img.shape[1] // 2:
                idx = self.arch_handler.L_canal_spline.add_cp(mouse_x, mouse_y)
                self.arch_handler.history.add(LeftCanalCpAddedAction((mouse_x, mouse_y), idx))
            else:
                idx = self.arch_handler.R_canal_spline.add_cp(mouse_x, mouse_y)
                self.arch_handler.history.add(RightCanalCpAddedAction((mouse_x, mouse_y), idx))

    def mousePressEvent(self, QMouseEvent):
        if not self._can_edit_spline:
            return

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
            self.handle_right_click(mouse_x, mouse_y)

    def mouseReleaseEvent(self, QMouseEvent):
        if not self._can_edit_spline:
            return

        self.drag_point = None
        if self.action is not None:
            self.spline_changed.emit()
            self.arch_handler.history.add(self.action)
            self.action = None
        self.update()

    def mouseMoveEvent(self, QMouseEvent):
        if not self._can_edit_spline:
            return

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

    def show_(self, pos=None):
        self.current_pos = pos
        self.set_img()
        self.update()


class SinglePanorexWidget(QtGui.QWidget):
    def __init__(self, parent):
        super(SinglePanorexWidget, self).__init__()
        self.parent = parent

        self.arch_handler = ArchHandler()

        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.pano = QtWidgets.QLabel(self)
        self.pano.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.pano)

    def show_(self, panorex=None, pos=None):
        if panorex is None:
            panorex = self.arch_handler.get_panorex()

        if pos is not None:
            panorex = draw_blue_vertical_line(panorex, pos)

        pixmap = numpy2pixmap(panorex)
        self.pano.setPixmap(pixmap)
        self.pano.update()


class PanorexWidget(QtGui.QWidget):
    def __init__(self, parent):
        super(PanorexWidget, self).__init__()
        self.parent = parent

        self.arch_handler = ArchHandler()

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

    def show_(self, pos=None):
        panorex = self.arch_handler.get_panorex()
        l_panorex, h_panorex = self.arch_handler.get_LH_panorexes()

        self.h_pano.show_(h_panorex, pos)
        self.m_pano.show_(panorex, pos)
        self.l_pano.show_(l_panorex, pos)
