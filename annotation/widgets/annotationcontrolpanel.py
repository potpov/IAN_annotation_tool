from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui

from annotation.components.PrevNextButtons import PrevNextButtons
from annotation.components.Slider import Slider


class AnnotationControlPanelWidget(QtGui.QWidget):
    pos_changed = QtCore.pyqtSignal()
    flags_changed = QtCore.pyqtSignal()
    acquire_annotation_clicked = QtCore.pyqtSignal()
    reset_annotation_clicked = QtCore.pyqtSignal()
    show_result_clicked = QtCore.pyqtSignal()

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

        self.prev_next_btns = PrevNextButtons()
        self.prev_next_btns.prev_clicked.connect(lambda: self.pos_slider.setValue(self.pos_slider.value() - 1))
        self.prev_next_btns.next_clicked.connect(lambda: self.pos_slider.setValue(self.pos_slider.value() + 1))
        self.layout.addRow(QtWidgets.QLabel(" "), self.prev_next_btns)

        self.show_dot = QtWidgets.QCheckBox("Show dot (D)")
        self.show_dot.setChecked(True)
        self.show_dot.setShortcut("D")
        self.show_dot.clicked.connect(self.flags_changed.emit)
        self.layout.addRow(QtWidgets.QLabel(""), self.show_dot)

        self.show_hint = QtWidgets.QCheckBox("Show hint (H)")
        self.show_hint.setChecked(False)
        self.show_hint.setShortcut("H")
        self.show_hint.clicked.connect(self.flags_changed.emit)
        self.layout.addRow(QtWidgets.QLabel(""), self.show_hint)

        self.show_mask_spline = QtWidgets.QCheckBox("Show mask spline (S)")
        self.show_mask_spline.setChecked(True)
        self.show_mask_spline.setShortcut("S")
        self.show_mask_spline.clicked.connect(self.flags_changed.emit)
        self.layout.addRow(QtWidgets.QLabel(""), self.show_mask_spline)

        self.auto_acquire_annotation = QtWidgets.QCheckBox(
            "Automatically acquire annotation from previous/succeeding (Ctrl+A)")
        self.auto_acquire_annotation.setChecked(False)
        self.auto_acquire_annotation.setShortcut("Ctrl+A")
        self.auto_acquire_annotation.clicked.connect(self.flags_changed.emit)
        self.layout.addRow(QtWidgets.QLabel(""), self.auto_acquire_annotation)

        self.acquire_annotation = QtWidgets.QPushButton("Acquire annotation from previous/succeeding (A)")
        self.acquire_annotation.setShortcut("A")
        self.acquire_annotation.clicked.connect(self.acquire_annotation_clicked.emit)
        self.layout.addRow(QtWidgets.QLabel(""), self.acquire_annotation)

        self.reset_annotation = QtWidgets.QPushButton("Reset current annotation (R)")
        self.reset_annotation.clicked.connect(self.reset_annotation_clicked.emit)
        self.reset_annotation.setShortcut("R")
        self.layout.addRow(QtWidgets.QLabel(""), self.reset_annotation)

        self.show_result = QtWidgets.QPushButton("Show result")
        self.show_result.clicked.connect(self.show_result_clicked.emit)
        self.layout.addRow(QtWidgets.QLabel(""), self.show_result)

    ###########
    # Getters #
    ###########

    def getPosValue(self):
        return self.pos_slider.value()

    def setPosSliderMaximum(self, new_maximum):
        maximum = self.pos_slider.maximum()
        if maximum == 0 or maximum != new_maximum:
            self.pos_slider.setMaximum(new_maximum)
