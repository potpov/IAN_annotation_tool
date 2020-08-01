from PyQt5 import QtCore
from pyface.qt import QtGui
import qtawesome as qta
from annotation.utils import numpy2pixmap
from annotation.widgets.archpanocontrolpanel import ArchPanoControlPanelWidget
from annotation.widgets.archview import SplineArchWidget
from annotation.widgets.panorex import PanorexWidget
from annotation.widgets.sidevolume import SideVolume


class ArchPanorexContainerWidget(QtGui.QWidget):

    def __init__(self, parent):
        super(ArchPanorexContainerWidget, self).__init__()
        self.parent = parent
        self.layout = QtGui.QGridLayout(self)

        # --- toolbar ---
        self.toolbar = QtGui.QToolBar()
        self.toolbar.setIconSize(QtCore.QSize(32, 32))

        # save
        save_action = QtGui.QAction(qta.icon('fa5s.save'), "Save", self)
        save_action.triggered.connect(self.save)
        self.toolbar.addAction(save_action)
        # load
        load_action = QtGui.QAction(qta.icon('fa5s.file-upload'), "Load", self)
        load_action.triggered.connect(self.load)
        self.toolbar.addAction(load_action)

        self.layout.setMenuBar(self.toolbar)
        # --- end toolbar ---

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

        self.arch_handler = None
        self.current_pos = 0

    def initialize(self):
        self.archview.img = self.arch_handler.get_section(self.arch_handler.selected_slice)
        self.archview.pixmap = numpy2pixmap(self.archview.img)

    def save(self):
        self.arch_handler.save_state()

    def load(self):
        self.arch_handler.load_state()
        self.spline_changed()

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
