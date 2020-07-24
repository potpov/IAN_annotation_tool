from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui

from annotation.components.Slider import Slider
from annotation.utils import numpy2pixmap
from annotation.widgets.archpanocontrolpanel import ArchPanoControlPanelWidget
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

        # control panel
        self.panel = ArchPanoControlPanelWidget()
        self.panel.pos_changed.connect(self.pos_changed_handler)
        self.panel.arch_changed.connect(self.arch_changed_handler)
        self.panel.pano_offset_changed.connect(self.pano_offset_changed_handler)
        self.panel.update_side_volume.connect(self.update_side_volume_handler)
        self.layout.addWidget(self.panel, 1, 0)

        self.arch_handler = None
        self.current_pos = 0

    def initialize(self):
        self.archview.img = self.arch_handler.get_section(self.arch_handler.selected_slice)
        self.archview.pixmap = numpy2pixmap(self.archview.img)

    def spline_changed(self):
        self.arch_handler.update_coords()
        self.arch_handler.compute_side_coords()
        self.arch_handler.compute_offsetted_arch(offset_amount=self.panel.getArchValue())
        self.arch_handler.compute_panorexes(coords=self.arch_handler.offsetted_arch,
                                            arch_offset=self.panel.getPanoOffsetValue())
        self.show_img()

    def pos_changed_handler(self):
        self.current_pos = self.panel.getPosValue()
        self.show_img()

    def arch_changed_handler(self):
        self.arch_handler.compute_offsetted_arch(offset_amount=self.panel.getArchValue())
        self.arch_handler.compute_panorexes(coords=self.arch_handler.offsetted_arch,
                                            arch_offset=self.panel.getPanoOffsetValue())
        self.show_img()

    def pano_offset_changed_handler(self):
        self.arch_handler.compute_panorexes(coords=self.arch_handler.offsetted_arch,
                                            arch_offset=self.panel.getPanoOffsetValue())
        self.show_img()

    def update_side_volume_handler(self):
        self.arch_handler.compute_side_volume()
        self.show_img()

    def set_arch_handler(self, arch_handler):
        self.arch_handler = arch_handler
        self.archview.arch_handler = arch_handler
        self.panorex.arch_handler = arch_handler
        self.sidevolume.arch_handler = arch_handler

    def show_img(self):
        self.panel.setPosSliderMaximum(len(self.arch_handler.offsetted_arch) - 1)
        self.archview.show_arch(pos=self.current_pos)
        self.panorex.show_panorex(pos=self.current_pos)
        self.sidevolume.show_side_view(pos=self.current_pos)
