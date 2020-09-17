from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui

from annotation.components.PrevNextButtons import PrevNextButtons
from annotation.components.Slider import Slider


class ArchSplineControlPanel(QtGui.QWidget):
    pos_changed = QtCore.pyqtSignal()
    arch_changed = QtCore.pyqtSignal()
    pano_offset_changed = QtCore.pyqtSignal()
    update_side_volume = QtCore.pyqtSignal()

    def __init__(self):
        super(ArchSplineControlPanel, self).__init__()
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

        self.prev_next_btns = PrevNextButtons()
        self.prev_next_btns.prev_clicked.connect(lambda: self.pos_slider.setValue(self.pos_slider.value() - 1))
        self.prev_next_btns.next_clicked.connect(lambda: self.pos_slider.setValue(self.pos_slider.value() + 1))
        self.layout.addRow(QtWidgets.QLabel(" "), self.prev_next_btns)

        self.update_side_volume_btn = QtWidgets.QPushButton("Update side volume")
        self.update_side_volume_btn.clicked.connect(self.update_side_volume.emit)
        self.layout.addRow(QtWidgets.QLabel("Side volume"), self.update_side_volume_btn)

        self.arch_slider = Slider(QtCore.Qt.Horizontal)
        self.arch_slider.setRange(-50, 50)
        self.arch_slider.setValue(0)
        self.arch_slider.setDefaultValue(0)
        self.arch_slider.setTickPosition(QtWidgets.QSlider.TicksAbove)
        self.arch_slider.setTickInterval(10)
        self.arch_slider.valueChanged.connect(self.arch_changed.emit)
        self.layout.addRow(QtWidgets.QLabel("Arch"), self.arch_slider)

        self.pano_offset_slider = Slider(QtCore.Qt.Horizontal)
        self.pano_offset_slider.setRange(1, 10)
        self.pano_offset_slider.setValue(1)
        self.pano_offset_slider.setDefaultValue(1)
        self.pano_offset_slider.setTickPosition(QtWidgets.QSlider.TicksAbove)
        self.pano_offset_slider.setTickInterval(1)
        self.pano_offset_slider.valueChanged.connect(self.pano_offset_changed.emit)
        self.layout.addRow(QtWidgets.QLabel("Panorex offset"), self.pano_offset_slider)

    ###########
    # Getters #
    ###########

    def getPosValue(self):
        return self.pos_slider.value()

    def getArchValue(self):
        return self.arch_slider.value()

    def getPanoOffsetValue(self):
        return self.pano_offset_slider.value()

    ###########
    # Setters #
    ###########

    def setPosSliderMaximum(self, new_maximum):
        maximum = self.pos_slider.maximum()
        if maximum == 0 or maximum != new_maximum:
            self.pos_slider.setMaximum(new_maximum)
