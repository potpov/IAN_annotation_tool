from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui

from annotation.utils import numpy2pixmap


class SliceSelectionWidget(QtGui.QWidget):
    def __init__(self, parent):
        super(SliceSelectionWidget, self).__init__()
        self.container = parent
        self.arch_handler = None

        # layout setup
        self.layout = QtGui.QGridLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # slider setup
        self.slider = QtWidgets.QSlider(self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)
        self.slider.setValue(0)
        self.slider.setTickPosition(QtWidgets.QSlider.TicksLeft)
        self.slider.setTickInterval(10)
        self.slider.valueChanged.connect(self.slider_value_changed)
        self.slider.setMaximumWidth(50)
        self.layout.addWidget(self.slider, 0, 0)

        # slider line edit setup
        self.slider_edit = QtGui.QLineEdit(self)
        self.slider_edit.setText(str(self.slider.value))
        self.slider_edit.textChanged.connect(self.slider_edit_value_changed)
        self.slider_edit.setMaximumWidth(50)
        self.layout.addWidget(self.slider_edit, 1, 0)

        # label setup
        self.label_img = QtWidgets.QLabel(self)
        self.label_img.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.label_img, 0, 1)

        # arch checkbox setup
        self.arch_line = QtWidgets.QCheckBox("Arch")
        self.arch_line.setChecked(False)
        self.arch_line.toggled.connect(self.toggle_arch_line)
        self.layout.addWidget(self.arch_line, 1, 1)

        # confirm slice button
        self.confirm_button = QtWidgets.QPushButton(self, text="Confirm")
        self.confirm_button.clicked.connect(lambda x: self.container.slice_selected.emit(self.slider.value()))
        self.layout.addWidget(self.confirm_button, 1, 2)

    def slider_edit_value_changed(self):
        try:
            val = int(self.slider_edit.text())
        except:
            val = 0
        val = max(self.slider.minimum(), min(val, self.slider.maximum()))
        self.slider.setValue(val)

    def slider_value_changed(self):
        val = self.slider.value()
        self.slider_edit.setText(str(val))
        slice = self.arch_handler.get_section(val, arch=self.arch_line.isChecked(), offsets=False)
        self.set_img(slice)

    def set_img(self, img):
        if self.slider.maximum() == 0:
            max = self.arch_handler.volume.shape[0]
            self.slider.setMaximum(max - 1)
            self.slider.setValue(96)

        pixmap = numpy2pixmap(img)
        self.label_img.setPixmap(pixmap)
        self.label_img.update()

    def toggle_arch_line(self):
        val = self.slider.value()
        slice = self.arch_handler.get_section(val, arch=self.arch_line.isChecked())
        self.set_img(slice)
