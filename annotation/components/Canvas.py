from PyQt5 import QtCore
from pyface.qt import QtGui
from abc import ABCMeta, abstractmethod


class CanvasMeta(type(QtCore.QObject), ABCMeta):
    pass


class Canvas(QtGui.QWidget, metaclass=CanvasMeta):
    def __init__(self, parent):
        super(Canvas, self).__init__()
        self.layout = QtGui.QHBoxLayout(self)
        self.container = parent
        self.img = None
        self.pixmap = None

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.draw(qp)
        qp.end()

    @abstractmethod
    def set_img(self):
        pass

    @abstractmethod
    def draw(self):
        pass

    @abstractmethod
    def show_(self):
        pass


class SplineCanvas(Canvas, metaclass=CanvasMeta):
    def __init__(self, parent):
        super().__init__(parent)
        self.l = 8  # size of the side of the square for the control points
        self.drag_point = None

    @abstractmethod
    def mousePressEvent(self, QMouseEvent):
        pass

    @abstractmethod
    def mouseReleaseEvent(self, QMouseEvent):
        pass

    @abstractmethod
    def mouseMoveEvent(self, QMouseEvent):
        pass
