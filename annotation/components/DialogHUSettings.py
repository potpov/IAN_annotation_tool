from PyQt5 import QtCore, QtWidgets
from pyface.qt import QtGui
import numpy as np

from annotation.core.ArchHandler import ArchHandler
from annotation.utils.ContrastStretching import ContrastStretching
from annotation.utils.qt import numpy2pixmap
from annotation.controlpanels.ControlPanel import ControlPanel


class DialogHUSettings(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(DialogHUSettings, self).__init__(parent)

        self.setWindowTitle("Hounsfield Units thresholds")
        self.setMinimumWidth(500)
        self.layout = QtGui.QVBoxLayout(self)
        self.cs = ContrastStretching()

        self.test_image = self.create_test_image()
        self.test_image_label = QtGui.QLabel()
        self.test_image_label.setPixmap(numpy2pixmap(self.test_image))

        self.arch_handler = ArchHandler()
        min_, max_ = self.arch_handler.get_min_max_HU()

        self.min_slider = ControlPanel().create_slider(name="Lower threshold", min=min_, max=max_,
                                                       val=self.cs.min_, default=min_,
                                                       tick_interval=100,
                                                       valueChanged=self.min_slider_changed_handler)
        self.max_slider = ControlPanel().create_slider(name="Higher threshold", min=min_, max=max_,
                                                       val=self.cs.max_, default=max_,
                                                       tick_interval=100,
                                                       valueChanged=self.max_slider_changed_handler)
        self.close_button = QtGui.QPushButton("Close")
        self.close_button.clicked.connect(self.close)

        self.layout.addWidget(self.test_image_label)
        self.layout.addWidget(self.min_slider)
        self.layout.addWidget(self.max_slider)
        self.layout.addWidget(self.close_button)

    def update_test_image(self):
        self.test_image_label.setPixmap(numpy2pixmap(self.test_image))

    def min_slider_changed_handler(self):
        if self.min_slider.value() > self.max_slider.value():
            self.min_slider.setValue(self.max_slider.value())
        self.cs.set_min(self.min_slider.value())
        self.update_test_image()

    def max_slider_changed_handler(self):
        if self.max_slider.value() < self.min_slider.value():
            self.max_slider.setValue(self.min_slider.value())
        self.cs.set_max(self.max_slider.value())
        self.update_test_image()

    def create_test_image(self):
        return np.tile(np.arange(0, 255).repeat(2), (100, 1)).astype(np.float32) / 255
