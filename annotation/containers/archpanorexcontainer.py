from PyQt5 import QtCore, QtWidgets
from pyface.qt import QtGui
import qtawesome as qta
from annotation.widgets.archpanocontrolpanel import ArchPanoControlPanelWidget
from annotation.widgets.archview import SplineArchWidget
from annotation.widgets.panorex import PanorexWidget
from annotation.widgets.sidevolume import SideVolume
from annotation.widgets.toolbar import Toolbar


class ArchPanorexContainerWidget(QtGui.QWidget):
    spline_selected = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        super(ArchPanorexContainerWidget, self).__init__()
        self.parent = parent
        self.layout = QtGui.QGridLayout(self)

        # toolbar
        self.toolbar = Toolbar()
        self.toolbar.toolbar_load.connect(self.spline_changed)
        self.layout.setMenuBar(self.toolbar.bar)

        # arch view
        self.archview = SplineArchWidget(self)
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

        # confirm
        self.confirm_button = QtWidgets.QPushButton(self, text="Confirm (C)")
        self.confirm_button.setShortcut("C")
        self.confirm_button.clicked.connect(self.spline_selected.emit)
        self.layout.addWidget(self.confirm_button, 1, 2)

        self.arch_handler = None
        self.current_pos = 0

    def initialize(self):
        self.archview.set_img()

    def spline_changed(self):
        self.arch_handler.update_coords()
        self.arch_handler.compute_side_coords()
        self.arch_handler.compute_offsetted_arch(offset_amount=self.panel.getArchValue(),
                                                 arch_offset=self.panel.getPanoOffsetValue())
        self.arch_handler.compute_panorexes()
        self.show_img()

    def pos_changed_handler(self):
        self.current_pos = self.panel.getPosValue()
        self.show_img()

    def arch_changed_handler(self):
        self.arch_handler.compute_offsetted_arch(offset_amount=self.panel.getArchValue(),
                                                 arch_offset=self.panel.getPanoOffsetValue())
        self.arch_handler.compute_panorexes()
        self.show_img()

    def pano_offset_changed_handler(self):
        self.arch_handler.compute_offsetted_arch(offset_amount=self.panel.getArchValue(),
                                                 arch_offset=self.panel.getPanoOffsetValue())
        self.arch_handler.compute_panorexes()
        self.show_img()

    def update_side_volume_handler(self):
        self.arch_handler.compute_side_volume_dialog(scale=3)
        self.show_img()

    def set_arch_handler(self, arch_handler):
        self.arch_handler = arch_handler
        self.toolbar.arch_handler = arch_handler
        self.archview.arch_handler = arch_handler
        self.panorex.arch_handler = arch_handler
        self.sidevolume.arch_handler = arch_handler

    def show_img(self):
        self.panel.setPosSliderMaximum(len(self.arch_handler.offsetted_arch) - 1)
        self.archview.show_(pos=self.current_pos)
        self.panorex.show_(pos=self.current_pos)
        self.sidevolume.show_(pos=self.current_pos)
