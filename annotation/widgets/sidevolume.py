from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui

from annotation import WIDGET_MARGIN
from annotation.components.Canvas import SplineCanvas
from annotation.spline.spline import ClosedSpline
from annotation.tests.opencv_tests.test_image_processing import extimate_canal
from annotation.utils import numpy2pixmap, clip_range


class CanvasSideVolume(SplineCanvas):
    def __init__(self, parent):
        super().__init__(parent)
        self.arch_handler = None
        self.current_pos = 0
        self.r = 3
        self.show_dot = True

    def set_img(self):
        self.img = self.arch_handler.side_volume[self.current_pos]
        self.pixmap = numpy2pixmap(self.img)
        self.setFixedSize(self.img.shape[1] + 50, self.img.shape[0] + 50)

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.draw(qp)
        qp.end()

    def draw(self, painter):
        if self.arch_handler is None:
            return
        if self.arch_handler.side_volume is None:
            return

        self.draw_background(painter)

        if self.show_dot:
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
                return

            x = WIDGET_MARGIN + self.pixmap.width() // 2

            img_canal, hull, mask = extimate_canal(self.img.copy(), (x - WIDGET_MARGIN, z - WIDGET_MARGIN))
            if hull is not None:
                for point in hull:
                    hx, hy = point[0]
                    painter.setPen(QtGui.QColor(200, 121, 219))
                    painter.drawEllipse(QtCore.QPoint(WIDGET_MARGIN + hx, WIDGET_MARGIN + hy), self.r, self.r)

            color = QtGui.QColor(255, 0, 0) if LR == "L" else QtGui.QColor(0, 0, 255)
            painter.setPen(color)
            painter.drawPoint(WIDGET_MARGIN + self.pixmap.width() // 2, z)
            color.setAlpha(100)
            painter.setBrush(color)
            painter.drawEllipse(QtCore.QPoint(x, z), self.r, self.r)

        # draw mask spline
        spline = self.arch_handler.annotation_masks.get_mask_spline(self.current_pos)
        if spline is None:
            return

        self.draw_spline(painter, spline, QtGui.QColor(0, 255, 0))

    def cp_clicked(self, spline, mouse_x, mouse_y):
        for cp_index, (point_x, point_y) in enumerate(spline.cp):
            if abs(point_x - mouse_x) < self.l // 2 and abs(point_y - mouse_y) < self.l // 2:
                return cp_index
        return None

    def handle_right_click(self, mouse_x, mouse_y):
        spline = self.arch_handler.annotation_masks.get_mask_spline(self.current_pos)
        if spline is None:
            spline = ClosedSpline([])

        idx_to_remove = self.cp_clicked(spline, mouse_x, mouse_y)
        if idx_to_remove is not None:
            spline.remove_cp(idx_to_remove)
        else:
            spline.add_cp(mouse_x, mouse_y)

        self.arch_handler.annotation_masks.set_mask_spline(self.current_pos, spline)

    def mousePressEvent(self, QMouseEvent):
        self.drag_point = None
        mouse_pos = QMouseEvent.pos()
        mouse_x = mouse_pos.x() - WIDGET_MARGIN
        mouse_y = mouse_pos.y() - WIDGET_MARGIN
        spline = self.arch_handler.annotation_masks.get_mask_spline(self.current_pos)
        if QMouseEvent.button() == QtCore.Qt.LeftButton and spline is not None:
            for cp_index, (point_x, point_y) in enumerate(spline.cp):
                if abs(point_x - mouse_x) < self.l // 2 and abs(point_y - mouse_y) < self.l // 2:
                    drag_x_offset = point_x - mouse_x
                    drag_y_offset = point_y - mouse_y
                    self.drag_point = (cp_index, (drag_x_offset, drag_y_offset))
        elif QMouseEvent.button() == QtCore.Qt.RightButton:
            self.handle_right_click(mouse_x, mouse_y)

    def mouseReleaseEvent(self, QMouseEvent):
        self.drag_point = None
        self.update()

    def mouseMoveEvent(self, QMouseEvent):
        spline = self.arch_handler.annotation_masks.get_mask_spline(self.current_pos)
        if spline is None:
            return

        if self.drag_point is not None:
            cp_index, (offset_x, offset_y) = self.drag_point
            new_x = QMouseEvent.pos().x() - WIDGET_MARGIN + offset_x
            new_y = QMouseEvent.pos().y() - WIDGET_MARGIN + offset_y

            new_x = clip_range(new_x, 0, self.pixmap.width() - 1)
            new_y = clip_range(new_y, 0, self.pixmap.height() - 1)

            # Set new point data

            new_idx = spline.update_cp(cp_index, new_x, new_y)
            self.drag_point = (new_idx, self.drag_point[1])

            # Redraw curve
            self.update()

    def show_(self, pos=0, show_dot=False):
        self.show_dot = show_dot
        self.current_pos = pos
        self.set_img()
        self.update()


class SideVolume(QtGui.QWidget):
    def __init__(self, parent):
        super(SideVolume, self).__init__()
        self.parent = parent

        self.arch_handler = None

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
            pixmap = numpy2pixmap(self.arch_handler.side_volume[pos])
            self.label.setPixmap(pixmap)
            self.label.update()
        except:
            pass
