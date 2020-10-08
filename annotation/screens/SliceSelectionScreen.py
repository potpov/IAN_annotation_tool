from PyQt5 import QtWidgets, QtCore
from annotation.screens.Screen import Screen
from annotation.utils.math import clip_range
from annotation.visualization.archview import ArchView
from annotation.controlpanels.ControlPanel import ControlPanel


class SliceSelectionScreen(Screen):
    slice_selected = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent)

        # slider
        self.slider = ControlPanel.create_slider("Slice", orientation=QtCore.Qt.Vertical,
                                                 max_h_w=100, valueChanged=self.show_)
        self.layout.addWidget(self.slider, 0, 1)

        # arch view
        self.archview = ArchView(self)
        self.layout.addWidget(self.archview, 0, 0)

        # arch checkbox
        self.arch_line = QtWidgets.QCheckBox("Arch")
        self.arch_line.setChecked(True)
        self.arch_line.toggled.connect(self.show_)
        self.layout.addWidget(self.arch_line, 1, 0)

        # confirm slice button
        self.confirm_button = QtWidgets.QPushButton(self, text="Confirm (C)")
        self.confirm_button.setShortcut("C")
        self.confirm_button.clicked.connect(lambda x: self.slice_selected.emit(self.slider.value()))
        self.layout.addWidget(self.confirm_button, 1, 1)

    def initialize(self):
        self.archview.set_img()
        if self.slider.maximum() == 0:
            max = self.arch_handler.Z - 1
            self.slider.setMaximum(max)
            self.slider.setValue(clip_range(96, 0, max))

    def show_(self):
        self.archview.show_(slice_idx=self.slider.value(), show_arch=self.arch_line.isChecked())
