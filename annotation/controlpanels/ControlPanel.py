from PyQt5 import QtCore, QtWidgets
from pyface.qt import QtGui
from annotation.components.Slider import Slider
from annotation.utils.metaclasses import AbstractQObjectMeta


class ControlPanel(QtGui.QWidget, metaclass=AbstractQObjectMeta):
    def __init__(self):
        """Control panel widget, usually used in Screen objects"""
        super(ControlPanel, self).__init__()
        self.layout = QtGui.QFormLayout(self)

    @staticmethod
    def create_slider(name=None, step=1, min=0, max=0, val=0, default=0, orientation=QtCore.Qt.Horizontal,
                      tick_interval=10, max_h_w=50, valueChanged=lambda: None, inverted=False):
        slider = Slider(orientation, name, step)
        slider.setMinimum(min)
        slider.setMaximum(max)
        slider.setValue(val)
        slider.setDefaultValue(default)
        slider.setInverted(inverted)
        slider.setTickInterval(tick_interval)
        if orientation == QtCore.Qt.Horizontal:
            slider.setTickPosition(QtWidgets.QSlider.TicksAbove)
            slider.setMaximumHeight(max_h_w)
        elif orientation == QtCore.Qt.Vertical:
            slider.setTickPosition(QtWidgets.QSlider.TicksRight)
            slider.setMaximumWidth(max_h_w)
        slider.valueChanged.connect(valueChanged)
        return slider
