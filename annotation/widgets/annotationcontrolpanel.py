from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui

from annotation.components.Slider import Slider


class AnnotationControlPanelWidget(QtGui.QWidget):
    pos_changed = QtCore.pyqtSignal()
    show_dot_toggled = QtCore.pyqtSignal()

    def __init__(self):
        super(AnnotationControlPanelWidget, self).__init__()
        self.layout = QtGui.QFormLayout(self)

        self.pos_slider = Slider(QtCore.Qt.Horizontal)
        self.pos_slider.setMinimum(0)
        self.pos_slider.setMaximum(0)
        self.pos_slider.setValue(0)
        self.pos_slider.setDefaultValue(0)
        self.pos_slider.setTickPosition(QtWidgets.QSlider.TicksAbove)
        self.pos_slider.setTickInterval(10)
        self.pos_slider.valueChanged.connect(self.pos_changed.emit)
        self.pos_slider.setMaximumHeight(50)
        self.layout.addRow(QtWidgets.QLabel("Position"), self.pos_slider)

        self.show_dot = QtWidgets.QCheckBox("")
        self.show_dot.setChecked(True)
        self.layout.addRow(QtWidgets.QLabel("Show dot"), self.show_dot)

    ###########
    # Getters #
    ###########

    def getPosValue(self):
        return self.pos_slider.value()

    def setPosSliderMaximum(self, new_maximum):
        maximum = self.pos_slider.maximum()
        if maximum == 0 or maximum != new_maximum:
            self.pos_slider.setMaximum(new_maximum)
