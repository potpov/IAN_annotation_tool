from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui

from annotation import WIDGET_MARGIN
from annotation.components.Canvas import SplineCanvas
from annotation.utils import numpy2pixmap, clip_range
from annotation.actions.Action import ArchCpChangedAction


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


class SplineArchWidget(SplineCanvas):
    spline_changed = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.arch_handler = None
        self.selected_slice = None
        self.current_pos = 0
        self.action = None  # action in progress

    def set_img(self):
        self.selected_slice = self.arch_handler.selected_slice
        self.img = self.arch_handler.get_section(self.selected_slice)
        self.pixmap = numpy2pixmap(self.img)
        self.setFixedSize(self.img.shape[1] + 50, self.img.shape[0] + 50)

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
        self.draw_points(painter, self.arch_handler.offsetted_arch, QtGui.QColor(0, 255, 255))
        self.draw_points(painter, l_pano, QtGui.QColor(0, 255, 255, 120))
        self.draw_points(painter, h_pano, QtGui.QColor(0, 255, 255, 120))
        self.draw_points(painter, l_offset, QtGui.QColor(0, 255, 0))
        self.draw_points(painter, h_offset, QtGui.QColor(0, 255, 0))

        # draw spline with control points
        self.draw_spline(painter, self.arch_handler.spline, QtGui.QColor(255, 0, 0), QtGui.QColor(0, 255, 0))

        # draw side_coords
        if self.current_pos >= len(self.arch_handler.side_coords):
            self.current_pos = len(self.arch_handler.side_coords) - 1
        self.draw_points(painter, self.arch_handler.side_coords[self.current_pos], QtGui.QColor(0, 0, 255))

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
