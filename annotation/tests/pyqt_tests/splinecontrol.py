import sys
import PyQt5.QtCore as QtCore
from pyface.qt import QtGui
import processing
from Jaw import Jaw
from annotation.spline.spline import Spline
from annotation.utils import numpy2pixmap


class SplineControlWidget(QtGui.QWidget):
    def __init__(self, parent, pixmap, coords):
        super(SplineControlWidget, self).__init__()
        self.container = parent
        self.coords = coords
        self.pixmap = pixmap
        self.num_cp = 20
        self.l = 8  # size of the side of the square for the control points
        self.curve = Spline(self.coords, self.num_cp)
        self.setGeometry(0, 0, self.pixmap.width(), self.pixmap.height())

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.draw(qp)
        qp.end()

    def draw(self, painter):
        painter.drawPixmap(QtCore.QRect(self.x(), self.y(), self.pixmap.width(), self.pixmap.height()), self.pixmap)
        for point in self.curve.get_spline():
            x, y = point
            painter.setPen(QtGui.QColor(255, 0, 0))
            painter.drawPoint(x + self.x(), y + self.y())
        for point in self.curve.cp:
            x, y = point
            painter.setPen(QtGui.QColor(0, 0, 255))
            painter.drawPoint(int(x + self.x()), int(y + self.y()))
            painter.setPen(QtGui.QColor(0, 255, 0))
            painter.setBrush(QtGui.QColor(0, 255, 0, 120))
            rect_x = int((x + self.x()) - (self.l / 2))
            rect_y = int((y + self.y()) - (self.l / 2))
            painter.drawRect(rect_x, rect_y, self.l, self.l)

    def mousePressEvent(self, QMouseEvent):
        """ Internal mouse-press handler """
        self._drag_point = None
        mouse_pos = QMouseEvent.pos()
        mouse_x = mouse_pos.x()
        mouse_y = mouse_pos.y()

        for cp_index, (x, y) in enumerate(self.curve.cp):
            point_x = x + self.x()
            point_y = y + self.y()
            if abs(point_x - mouse_x) < self.l:
                if (abs(point_y - mouse_y)) < self.l:
                    drag_x_offset = point_x - mouse_x
                    drag_y_offset = point_y - mouse_y
                    self._drag_point = (cp_index, (drag_x_offset, drag_y_offset))

        self.update()

    def mouseReleaseEvent(self, QMouseEvent):
        """ Internal mouse-release handler """
        self._drag_point = None

    def mouseMoveEvent(self, QMouseEvent):
        """ Internal mouse-move handler """
        if self._drag_point is not None:
            mouse_x = QMouseEvent.pos().x() - self._drag_point[1][0]
            mouse_y = QMouseEvent.pos().y() - self._drag_point[1][1]

            # Set new point data
            new_idx = self.curve.update_cp(self._drag_point[0], mouse_x, mouse_y)
            self._drag_point = (new_idx, self._drag_point[1])

            # Redraw curve
            self.update()


class Window(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.resize(500, 500)
        dicomdir_path = r"C:\Users\crime\Desktop\alveolar_nerve\dataset\DICOM_ANONIMI\PAZIENTE_3\PROVE3__19781222_DICOM\DICOMDIR"
        jaw = Jaw(dicomdir_path)
        self.selected_slice = 93
        self.slice = jaw.volume[self.selected_slice]
        pixmap = numpy2pixmap(self.slice)
        p, start, end = processing.arch_detection(self.slice)
        coords = processing.arch_lines(p, start, end)[1]
        self.widget = SplineControlWidget(self, pixmap, coords)
        self.setCentralWidget(self.widget)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    windows = Window()
    windows.show()
    app.exec_()
