from PyQt5 import QtWidgets, QtCore

from annotation.controlpanels.ControlPanel import ControlPanel


class SkipControlPanel(ControlPanel):
    skip_changed = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.skip = self.create_slider(valueChanged=lambda: self.skip_changed.emit(self.skip.value()))
        self.skip.valueChanged.connect(self.updateImagesCount)
        self.layout.insertRow(0, QtWidgets.QLabel("Skipped images"), self.skip)

        self.imgs_count = QtWidgets.QLabel("")
        self.updateImagesCount()

    def setSkipMaximum(self, new_maximum):
        maximum = self.skip.maximum()
        if maximum == 0 or maximum != new_maximum:
            self.skip.setMaximum(new_maximum)

    def setSkipValue(self, val):
        self.skip.setValue(val)
        self.updateImagesCount()

    def updateImagesCount(self):
        count = int(self.skip.maximum() / (self.skip.value() + 1))
        self.imgs_count = QtWidgets.QLabel(str(count))
        self.layout.removeRow(1)
        self.layout.insertRow(1, QtWidgets.QLabel("Number of images"), self.imgs_count)
