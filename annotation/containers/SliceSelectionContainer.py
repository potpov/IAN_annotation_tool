from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui

from annotation.components.Slider import Slider
from annotation.utils.qt import numpy2pixmap
from annotation.utils.math import clip_range
from annotation.visualization.archview import ArchView


class SliceSelectionContainer(QtGui.QWidget):
    slice_selected = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        super(SliceSelectionContainer, self).__init__()
        self.container = parent
        self.arch_handler = None

        # layout setup
        self.layout = QtGui.QGridLayout(self)

        self.slider = Slider(QtCore.Qt.Vertical, "Slice")
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)
        self.slider.setValue(0)
        self.slider.setDefaultValue(0)
        self.slider.setTickPosition(QtWidgets.QSlider.TicksRight)
        self.slider.setTickInterval(10)
        self.slider.valueChanged.connect(self.show_img)
        self.slider.setMaximumWidth(100)
        self.layout.addWidget(self.slider, 0, 1)

        self.archview = ArchView(self)
        self.layout.addWidget(self.archview, 0, 0)

        # arch checkbox setup
        self.arch_line = QtWidgets.QCheckBox("Arch")
        self.arch_line.setChecked(True)
        self.arch_line.toggled.connect(self.show_img)
        self.layout.addWidget(self.arch_line, 1, 0)

        # confirm slice button
        self.confirm_button = QtWidgets.QPushButton(self, text="Confirm (C)")
        self.confirm_button.setShortcut("C")
        self.confirm_button.clicked.connect(lambda x: self.slice_selected.emit(self.slider.value()))
        self.layout.addWidget(self.confirm_button, 1, 1)

    def initialize(self):
        self.archview.set_img()

    def set_arch_handler(self, arch_handler):
        self.arch_handler = arch_handler
        self.archview.arch_handler = arch_handler
        if self.slider.maximum() == 0:
            max = self.arch_handler.Z - 1
            self.slider.setMaximum(max)
            self.slider.setValue(clip_range(96, 0, max))

    def show_img(self):
        self.archview.show_(slice_idx=self.slider.value(), show_arch=self.arch_line.isChecked())
