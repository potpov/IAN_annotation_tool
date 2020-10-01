from PyQt5 import QtWidgets, QtCore
from annotation.components.PrevNextButtons import PrevNextButtons
from annotation.controlpanels.ControlPanel import ControlPanel


class ArchSplineControlPanel(ControlPanel):
    pos_changed = QtCore.pyqtSignal()
    arch_offset_changed = QtCore.pyqtSignal()
    pano_offset_changed = QtCore.pyqtSignal()
    update_side_volume = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

        self.pos_slider = self.create_slider(valueChanged=self.pos_changed.emit)
        self.layout.addRow(QtWidgets.QLabel("Position"), self.pos_slider)

        self.prev_next_btns = PrevNextButtons()
        self.prev_next_btns.prev_clicked.connect(lambda: self.pos_slider.setValue(self.pos_slider.value() - 1))
        self.prev_next_btns.next_clicked.connect(lambda: self.pos_slider.setValue(self.pos_slider.value() + 1))
        self.layout.addRow(QtWidgets.QLabel(" "), self.prev_next_btns)

        self.update_side_volume_btn = QtWidgets.QPushButton("Update side volume")
        self.update_side_volume_btn.clicked.connect(self.update_side_volume.emit)
        self.layout.addRow(QtWidgets.QLabel("Side volume"), self.update_side_volume_btn)

        self.arch_slider = self.create_slider(min=-50, max=50, valueChanged=self.arch_offset_changed.emit)
        self.layout.addRow(QtWidgets.QLabel("Arch"), self.arch_slider)

        self.pano_offset_slider = self.create_slider(min=1, max=10, val=1, default=1, tick_interval=1,
                                                     valueChanged=self.pano_offset_changed.emit)
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
