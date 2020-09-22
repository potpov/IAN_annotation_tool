import sys

import numpy as np
import PyQt5.QtCore as QtCore
from pyface.qt import QtGui
from Jaw import Jaw
from annotation.spline.CatmullRom import CHORDAL, UNIFORM, CENTRIPETAL
from annotation.spline.Spline import ClosedSpline
from annotation.utils.qt import numpy2pixmap
from annotation.utils.math import clip_range
from annotation.utils.image import plot, export_img, active_contour_balloon
from annotation.components.Canvas import SplineCanvas

WIDGET_MARGIN = 11


class SplineWidget(SplineCanvas):
    def __init__(self, parent, img):
        super().__init__(parent)
        self.spline = ClosedSpline()
        self.img = img
        self.pixmap = numpy2pixmap(img)
        self.adjust_size()
        self.snake = None

    def snake_button_clicked(self):
        spline = self.spline.get_spline()
        if len(spline) == 0:
            return
        init = np.array(spline)
        # self.snake = active_contour(self.img, init, max_iterations=100)
        self.snake = active_contour_balloon(self.img, self.spline, debug=True, threshold=10)
        self.spline = ClosedSpline(coords=self.snake, num_cp=self.spline.num_cp)
        self.update()

    def set_img(self):
        pass

    def draw(self, painter):
        self.draw_background(painter, WIDGET_MARGIN)
        # if self.snake is not None:
        #     self.draw_points(painter, self.snake, QtGui.QColor(0, 0, 255))
        self.draw_spline(painter, self.spline, QtGui.QColor(255, 0, 0), show_cp_idx=True, offsetXY=WIDGET_MARGIN)

    def show_(self):
        pass

    def cp_clicked(self, spline, mouse_x, mouse_y):
        for cp_index, (point_x, point_y) in enumerate(spline.cp):
            if abs(point_x - mouse_x) < self.l // 2 and abs(point_y - mouse_y) < self.l // 2:
                return cp_index
        return None

    def handle_right_click(self, mouse_x, mouse_y):
        idx_to_remove = self.cp_clicked(self.spline, mouse_x, mouse_y)
        if idx_to_remove is not None:
            self.spline.remove_cp(idx_to_remove)

        else:
            self.spline.add_cp(mouse_x, mouse_y)

    def mousePressEvent(self, QMouseEvent):
        """ Internal mouse-press handler """
        self.drag_point = None
        mouse_pos = QMouseEvent.pos()
        mouse_x = mouse_pos.x() - WIDGET_MARGIN
        mouse_y = mouse_pos.y() - WIDGET_MARGIN
        if QMouseEvent.button() == QtCore.Qt.LeftButton:
            for cp_index, (point_x, point_y) in enumerate(self.spline.cp):
                if abs(point_x - mouse_x) < self.l // 2 and abs(point_y - mouse_y) < self.l // 2:
                    drag_x_offset = point_x - mouse_x
                    drag_y_offset = point_y - mouse_y
                    self.drag_point = (cp_index, (drag_x_offset, drag_y_offset))
        elif QMouseEvent.button() == QtCore.Qt.RightButton:
            self.handle_right_click(mouse_x, mouse_y)

    def mouseReleaseEvent(self, QMouseEvent):
        """ Internal mouse-release handler """
        self.drag_point = None
        self.update()

    def mouseMoveEvent(self, QMouseEvent):
        """ Internal mouse-move handler """
        if self.drag_point is not None:
            cp_index, (offset_x, offset_y) = self.drag_point
            new_x = QMouseEvent.pos().x() - WIDGET_MARGIN + offset_x
            new_y = QMouseEvent.pos().y() - WIDGET_MARGIN + offset_y

            new_x = clip_range(new_x, 0, self.pixmap.width() - 1)
            new_y = clip_range(new_y, 0, self.pixmap.height() - 1)

            # Set new point data
            new_idx = self.spline.update_cp(cp_index, new_x, new_y)
            self.drag_point = (new_idx, self.drag_point[1])

            # Redraw curve
            self.update()


class Container(QtGui.QWidget):

    def __init__(self):
        super(Container, self).__init__()

        dicomdir_path = r"C:\Users\crime\Desktop\alveolar_nerve\dataset\DICOM_ANONIMI\PAZIENTE_3\PROVE3__19781222_DICOM\DICOMDIR"
        jaw = Jaw(dicomdir_path)
        self.selected_slice = 93
        self.slice = jaw.volume[self.selected_slice]

        self.spline_widget = SplineWidget(self, self.slice)

        self.mask_button = QtGui.QPushButton("mask")
        self.mask_button.clicked.connect(self.mask_button_clicked)

        self.snake_button = QtGui.QPushButton("snake")
        self.snake_button.clicked.connect(self.spline_widget.snake_button_clicked)

        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.spline_widget)
        self.layout.addWidget(self.mask_button)
        self.layout.addWidget(self.snake_button)

    def mask_button_clicked(self):
        import uuid
        mask = self.spline_widget.spline.generate_mask(self.slice.shape)
        plot(mask)
        export_img(mask, 'tmp/mask_{}.jpg'.format(uuid.uuid4()))


class Window(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setContentsMargins(0, 0, 0, 0)
        self.container = Container()
        self.setCentralWidget(self.container)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    windows = Window()
    windows.show()
    app.exec_()
