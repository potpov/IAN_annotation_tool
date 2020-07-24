from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui

from annotation.utils import numpy2pixmap
from annotation.widgets.archview import SplineArchWidget as ArchViewWidget
from annotation.widgets.panorex import PanorexWidget
from annotation.widgets.sidevolume import SideVolume


class ArchPanorexContainerWidget(QtGui.QWidget):

    def __init__(self, parent):
        super(ArchPanorexContainerWidget, self).__init__()
        self.parent = parent
        self.layout = QtGui.QGridLayout(self)

        # arch view
        self.archview = ArchViewWidget(self)
        self.archview.spline_changed.connect(self.spline_changed)
        self.layout.addWidget(self.archview, 0, 0)

        # panorex
        self.panorex = PanorexWidget(self)
        self.layout.addWidget(self.panorex, 0, 1)

        # side volume
        self.sidevolume = SideVolume(self)
        self.layout.addWidget(self.sidevolume, 0, 2)

        # slider
        self.pos_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.pos_slider.setMinimum(0)
        self.pos_slider.setMaximum(0)
        self.pos_slider.setValue(0)
        self.pos_slider.setTickPosition(QtWidgets.QSlider.TicksAbove)
        self.pos_slider.setTickInterval(10)
        self.pos_slider.valueChanged.connect(self.pos_slider_changed)
        self.pos_slider.setMaximumHeight(50)
        self.layout.addWidget(self.pos_slider, 1, 0)

        # slider
        self.arch_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.arch_slider.setMinimum(-50)
        self.arch_slider.setMaximum(50)
        self.arch_slider.setValue(0)
        self.arch_slider.setTickPosition(QtWidgets.QSlider.TicksRight)
        self.arch_slider.setTickInterval(10)
        self.arch_slider.valueChanged.connect(self.arch_slider_changed)
        self.layout.addWidget(self.arch_slider, 2, 0)

        self.arch_handler = None
        self.current_pos = 0

    def initialize(self):
        self.archview.img = self.arch_handler.get_section(self.arch_handler.selected_slice)
        self.archview.pixmap = numpy2pixmap(self.archview.img)

    def spline_changed(self):
        self.arch_handler.update_coords()
        self.arch_handler.compute_side_coords()
        self.arch_handler.compute_offsetted_arch(offset_amount=self.arch_slider.value())
        self.arch_handler.compute_panorexes(coords=self.arch_handler.offsetted_arch)
        self.show_img()

    def pos_slider_changed(self):
        self.current_pos = self.pos_slider.value()
        self.show_img()

    def arch_slider_changed(self):
        self.arch_handler.compute_offsetted_arch(offset_amount=self.arch_slider.value())
        self.arch_handler.compute_panorexes(coords=self.arch_handler.offsetted_arch)
        self.show_img()

    def set_dicom_handler(self, arch_handler):
        self.arch_handler = arch_handler
        self.archview.arch_handler = arch_handler
        self.panorex.arch_handler = arch_handler
        self.sidevolume.arch_handler = arch_handler

    def show_img(self):
        max_slide = len(self.arch_handler.offsetted_arch) - 1
        if self.pos_slider.maximum() == 0 or self.pos_slider.maximum() != max_slide:
            self.pos_slider.setMaximum(max_slide)

        self.archview.show_arch(pos=self.current_pos)
        self.panorex.show_panorex(pos=self.current_pos)
        self.sidevolume.show_side_view(pos=self.current_pos)
