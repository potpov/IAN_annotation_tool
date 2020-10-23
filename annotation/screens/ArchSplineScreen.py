from PyQt5 import QtCore, QtWidgets

from annotation.screens.PanorexSplineScreen import PanorexSplineScreen
from annotation.screens.Screen import Screen
from annotation.controlpanels.ArchSplineControlPanel import ArchSplineControlPanel
from annotation.visualization.archview import SplineArchView
from annotation.visualization.panorex import MultiPanorex
from annotation.visualization.sidevolume import SideVolume


class ArchSplineScreen(Screen):
    spline_selected = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent)
        self.container.loaded.connect(self.spline_changed)
        self.current_pos = 0

        # arch view
        self.archview = SplineArchView(self)
        self.archview.spline_changed.connect(self.spline_changed)
        self.layout.addWidget(self.archview, 0, 0)

        # panorex
        self.panorex = MultiPanorex(self)
        self.layout.addWidget(self.panorex, 0, 1)

        # side volume
        self.sidevolume = SideVolume(self)
        self.layout.addWidget(self.sidevolume, 0, 2)

        # control panel
        self.panel = ArchSplineControlPanel()
        self.panel.pos_changed.connect(self.pos_changed_handler)
        self.panel.arch_offset_changed.connect(self.offset_changed_handler)
        self.panel.pano_offset_changed.connect(self.offset_changed_handler)
        self.panel.update_side_volume.connect(self.update_side_volume_handler)
        self.layout.addWidget(self.panel, 1, 0, 1, 2)

        # confirm
        self.confirm_button = QtWidgets.QPushButton(self, text="Confirm (C)")
        self.confirm_button.setShortcut("C")
        self.confirm_button.clicked.connect(self.spline_selected.emit)
        self.layout.addWidget(self.confirm_button, 1, 2)

    def initialize(self):
        self.mb.enable_save_load(True)
        self.archview.set_img()

    def spline_changed(self):
        self.arch_handler.update_coords()
        self.arch_handler.compute_side_coords()
        self.offset_changed_handler()

    def pos_changed_handler(self):
        self.current_pos = self.panel.getPosValue()
        self.show_()

    def offset_changed_handler(self):
        self.arch_handler.offset_arch(arch_offset=self.panel.getArchValue(),
                                      pano_offset=self.panel.getPanoOffsetValue())
        self.show_()

    def update_side_volume_handler(self):
        self.arch_handler.compute_side_volume(self.arch_handler.SIDE_VOLUME_SCALE)
        self.show_()

    def show_(self):
        self.panel.setPosSliderMaximum(len(self.arch_handler.arch.get_arch()) - 1)
        self.archview.show_(pos=self.current_pos)
        self.panorex.show_(pos=self.current_pos)
        self.sidevolume.show_(pos=self.current_pos)

    def connect_signals(self):
        self.spline_selected.connect(self.next_screen)
        
    def next_screen(self):
        self.container.transition_to(PanorexSplineScreen)
