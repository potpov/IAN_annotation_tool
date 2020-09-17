from PyQt5 import QtCore

from annotation.utils.margin import WIDGET_MARGIN
import annotation.utils.colors as col
from annotation.components.Canvas import SplineCanvas, Canvas
from annotation.utils.qt import numpy2pixmap
from annotation.utils.math import clip_range
from annotation.actions.Action import ArchCpChangedAction


class ArchView(Canvas):
    def __init__(self, parent):
        super(ArchView, self).__init__(parent)
        self.arch_handler = None
        self.slice_idx = 0

    def set_img(self):
        self.img = self.arch_handler.volume[self.slice_idx]
        self.pixmap = numpy2pixmap(self.img)
        self.adjust_size()

    def draw(self, painter):
        p, start, end = self.arch_handler.get_arch_detection(self.slice_idx)
        self.draw_background(painter)
        self.draw_poly_approx(painter, p, start, end, col.ARCH_SPLINE)

    def show_(self, slice_idx=0, show_arch=True):
        self.slice_idx = slice_idx
        self.show_arch = show_arch
        self.set_img()
        self.update()


class SplineArchView(SplineCanvas):
    spline_changed = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.arch_handler = None
        self.selected_slice = None
        self.current_pos = 0
        self.action = None  # action in progress

    def set_img(self):
        self.selected_slice = self.arch_handler.selected_slice
        self.img = self.arch_handler.volume[self.selected_slice]
        self.pixmap = numpy2pixmap(self.img)
        self.adjust_size()

    def draw(self, painter):
        # when the widget is deleted, the painter may be updated anyway, even after the arch_handler reset
        if self.arch_handler is None:
            return
        if self.arch_handler.coords is None:
            return

        # draw pixmap
        self.draw_background(painter)

        l_offset, coords, h_offset, derivative = self.arch_handler.coords
        l_pano, h_pano = self.arch_handler.LHoffsetted_arches

        # draw arches
        self.draw_points(painter, self.arch_handler.offsetted_arch, col.PANO_SPLINE)
        self.draw_points(painter, l_pano, col.PANO_OFF_SPLINE)
        self.draw_points(painter, h_pano, col.PANO_OFF_SPLINE)
        self.draw_points(painter, l_offset, col.ARCH_OFF_SPLINE)
        self.draw_points(painter, h_offset, col.ARCH_OFF_SPLINE)

        # draw spline with control points
        self.draw_spline(painter, self.arch_handler.spline, col.ARCH_SPLINE, col.ARCH_SPLINE_CP)

        # draw side_coords
        if self.current_pos >= len(self.arch_handler.side_coords):
            self.current_pos = len(self.arch_handler.side_coords) - 1
        self.draw_points(painter, self.arch_handler.side_coords[self.current_pos], col.POS)

    def mousePressEvent(self, QMouseEvent):
        """ Internal mouse-press handler """
        self.drag_point = None
        self.action = None
        mouse_pos = QMouseEvent.pos()
        mouse_x = mouse_pos.x() - WIDGET_MARGIN
        mouse_y = mouse_pos.y() - WIDGET_MARGIN

        for cp_index, (point_x, point_y) in enumerate(self.arch_handler.spline.cp):
            if abs(point_x - mouse_x) < self.l // 2 and abs(point_y - mouse_y) < self.l // 2:
                drag_x_offset = point_x - mouse_x
                drag_y_offset = point_y - mouse_y
                self.drag_point = (cp_index, (drag_x_offset, drag_y_offset))
                self.action = ArchCpChangedAction((point_x, point_y), (point_x, point_y), cp_index)
                break

    def mouseReleaseEvent(self, QMouseEvent):
        """ Internal mouse-release handler """
        self.drag_point = None
        if self.action is not None:
            self.arch_handler.history.add(self.action)
            self.action = None
        self.spline_changed.emit()

    def mouseMoveEvent(self, QMouseEvent):
        """ Internal mouse-move handler """
        if self.drag_point is not None:
            cp_index, (offset_x, offset_y) = self.drag_point
            new_x = QMouseEvent.pos().x() - WIDGET_MARGIN + offset_x
            new_y = QMouseEvent.pos().y() - WIDGET_MARGIN + offset_y

            new_x = clip_range(new_x, 0, self.pixmap.width() - 1)
            new_y = clip_range(new_y, 0, self.pixmap.height() - 1)

            self.action = ArchCpChangedAction((new_x, new_y), self.action.prev, cp_index)

            # Set new point data
            new_idx = self.arch_handler.spline.update_cp(cp_index, new_x, new_y)
            self.drag_point = (new_idx, self.drag_point[1])

            # Redraw curve
            self.update()

    def show_(self, pos=None):
        self.current_pos = pos
        if self.selected_slice != self.arch_handler.selected_slice:
            self.set_img()
        self.update()
