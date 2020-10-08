from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui

from annotation.utils.margin import WIDGET_MARGIN
import annotation.utils.colors as col
from annotation.actions.Action import SideVolumeCpRemovedAction, SideVolumeCpAddedAction, SideVolumeCpChangedAction
from annotation.components.Canvas import SplineCanvas
from annotation.spline.Spline import ClosedSpline
from annotation.utils.math import clip_range
from annotation.utils.qt import numpy2pixmap
from annotation.core.ArchHandler import ArchHandler


class CanvasSideVolume(SplineCanvas):

    def __init__(self, parent):
        super().__init__(parent)
        self.arch_handler = ArchHandler()
        self.current_pos = 0
        self.r = 3

        # flags
        self.show_dot = False
        self.auto_propagate = False
        self.show_mask_spline = False

        # action
        self.action = None

    def set_img(self):
        self.img = self.arch_handler.get_side_volume_slice(self.current_pos)
        self.pixmap = numpy2pixmap(self.img)
        self.adjust_size()

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.draw(qp)
        qp.end()

    def extract_x_z_LR(self):
        x = WIDGET_MARGIN + self.pixmap.width() // 2
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
            return x, z, LR

        return x, z, LR

    def draw_dot(self, painter, x, z, LR):
        if z is None:
            return
        color = QtGui.QColor(col.L_CANAL_SPLINE if LR == "L" else col.R_CANAL_SPLINE)
        painter.setPen(color)
        painter.drawPoint(WIDGET_MARGIN + self.pixmap.width() // 2, z)
        color.setAlpha(120)
        painter.setBrush(color)
        painter.drawEllipse(QtCore.QPoint(x, z), self.r, self.r)

    def draw(self, painter):
        if self.arch_handler is None or self.arch_handler.side_volume is None:
            return

        self.draw_background(painter)

        x, z, LR = self.extract_x_z_LR()

        # draw mask spline
        if self.show_mask_spline:
            spline = self.arch_handler.annotation_masks.get_mask_spline(self.current_pos,
                                                                        from_snake=self.auto_propagate)
            self.draw_spline(painter, spline, col.ANN_SPLINE)

        if self.show_dot:
            self.draw_dot(painter, x, z, LR)

    def cp_clicked(self, spline, mouse_x, mouse_y):
        for cp_index, (point_x, point_y) in enumerate(spline.cp):
            if abs(point_x - mouse_x) < self.l // 2 and abs(point_y - mouse_y) < self.l // 2:
                return cp_index
        return None

    def handle_right_click(self, mouse_x, mouse_y):
        spline = self.arch_handler.annotation_masks.get_mask_spline(self.current_pos)
        if spline is None:
            spline = ClosedSpline()

        idx_to_remove = self.cp_clicked(spline, mouse_x, mouse_y)
        if idx_to_remove is not None:
            self.arch_handler.history.add(SideVolumeCpRemovedAction(idx_to_remove, self.current_pos))
            spline.remove_cp(idx_to_remove)
        else:
            added_cp_idx = spline.add_cp(mouse_x, mouse_y)
            self.arch_handler.history.add(SideVolumeCpAddedAction((mouse_x, mouse_y), added_cp_idx, self.current_pos))

        self.arch_handler.annotation_masks.set_mask_spline(self.current_pos, spline)

    def mousePressEvent(self, QMouseEvent):
        if not self._can_edit_spline:
            return

        # if we don't show the spline, then we don't react to clicks
        if not self.show_mask_spline:
            return

        self.drag_point = None
        self.action = None
        mouse_pos = QMouseEvent.pos()
        mouse_x = mouse_pos.x() - WIDGET_MARGIN
        mouse_y = mouse_pos.y() - WIDGET_MARGIN
        spline = self.arch_handler.annotation_masks.get_mask_spline(self.current_pos) or \
                 self.arch_handler.annotation_masks.set_mask_spline(self.current_pos, ClosedSpline(), from_snake=False)
        if QMouseEvent.button() == QtCore.Qt.LeftButton:
            for cp_index, (point_x, point_y) in enumerate(spline.cp):
                if abs(point_x - mouse_x) < self.l // 2 and abs(point_y - mouse_y) < self.l // 2:
                    drag_x_offset = point_x - mouse_x
                    drag_y_offset = point_y - mouse_y
                    self.drag_point = (cp_index, (drag_x_offset, drag_y_offset))
                    self.action = SideVolumeCpChangedAction((point_x, point_y), (point_x, point_y),
                                                            cp_index, self.current_pos)
                    break
        elif QMouseEvent.button() == QtCore.Qt.RightButton:
            self.handle_right_click(mouse_x, mouse_y)

    def mouseReleaseEvent(self, QMouseEvent):
        if not self._can_edit_spline:
            return

        self.drag_point = None
        if self.action is not None:
            self.arch_handler.history.add(self.action)
            self.action = None
        self.update()

    def mouseMoveEvent(self, QMouseEvent):
        if not self._can_edit_spline:
            return

        spline = self.arch_handler.annotation_masks.get_mask_spline(self.current_pos)
        if spline is None:
            return

        if self.drag_point is not None:
            cp_index, (offset_x, offset_y) = self.drag_point
            new_x = QMouseEvent.pos().x() - WIDGET_MARGIN + offset_x
            new_y = QMouseEvent.pos().y() - WIDGET_MARGIN + offset_y

            new_x = clip_range(new_x, 0, self.pixmap.width() - 1)
            new_y = clip_range(new_y, 0, self.pixmap.height() - 1)

            self.action = SideVolumeCpChangedAction((new_x, new_y), self.action.prev, cp_index, self.current_pos)

            # Set new point data
            new_idx = spline.update_cp(cp_index, new_x, new_y)
            self.drag_point = (new_idx, self.drag_point[1])

            # Redraw curve
            self.update()

    def show_(self, pos=0, show_dot=False, auto_propagate=False, show_mask_spline=False):
        self.current_pos = pos
        self.show_dot = show_dot
        self.auto_propagate = auto_propagate
        self.show_mask_spline = show_mask_spline
        self.set_img()
        self.update()


class SideVolume(QtGui.QWidget):
    def __init__(self, parent):
        super(SideVolume, self).__init__()
        self.parent = parent

        self.arch_handler = ArchHandler()

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
            pixmap = numpy2pixmap(self.arch_handler.get_side_volume_slice(pos))
            self.label.setPixmap(pixmap)
            self.label.update()
        except:
            pass
