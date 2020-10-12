from PyQt5 import QtWidgets, QtCore
from annotation.components.PrevNextButtons import PrevNextButtons
from annotation.controlpanels.ControlPanel import ControlPanel


class AnnotationControlPanel(ControlPanel):
    pos_changed = QtCore.pyqtSignal()
    flags_changed = QtCore.pyqtSignal()
    acquire_annotation_clicked = QtCore.pyqtSignal()
    reset_annotation_clicked = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

        self.pos_slider = self.create_slider(valueChanged=self.pos_changed.emit)
        self.layout.addRow(QtWidgets.QLabel("Position"), self.pos_slider)

        self.prev_next_btns = PrevNextButtons()
        self.layout.addRow(QtWidgets.QLabel(" "), self.prev_next_btns)

        self.show_dot = QtWidgets.QCheckBox("Show dot (D)")
        self.show_dot.setChecked(True)
        self.show_dot.setShortcut("D")
        self.show_dot.clicked.connect(self.flags_changed.emit)
        self.layout.addRow(QtWidgets.QLabel(""), self.show_dot)

        self.show_mask_spline = QtWidgets.QCheckBox("Show mask spline (S)")
        self.show_mask_spline.setChecked(True)
        self.show_mask_spline.setShortcut("S")
        self.show_mask_spline.clicked.connect(self.flags_changed.emit)
        self.layout.addRow(QtWidgets.QLabel(""), self.show_mask_spline)

        self.show_cp_boxes = QtWidgets.QCheckBox("Show control points (C)")
        self.show_cp_boxes.setChecked(True)
        self.show_cp_boxes.setShortcut("C")
        self.show_cp_boxes.clicked.connect(self.flags_changed.emit)
        self.layout.addRow(QtWidgets.QLabel(""), self.show_cp_boxes)

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

    ###########
    # Getters #
    ###########

    def setStep(self, step):
        try:
            self.prev_next_btns.prev_clicked.disconnect()
            self.prev_next_btns.next_clicked.disconnect()
        except:
            pass
        self.prev_next_btns.prev_clicked.connect(lambda: self.pos_slider.setValue(self.pos_slider.value() - step))
        self.prev_next_btns.next_clicked.connect(lambda: self.pos_slider.setValue(self.pos_slider.value() + step))
        self.pos_slider.setStep(step)

    def getPosValue(self):
        return self.pos_slider.value()

    def setPosSliderMaximum(self, new_maximum):
        maximum = self.pos_slider.maximum()
        if maximum == 0 or maximum != new_maximum:
            self.pos_slider.setMaximum(new_maximum)
