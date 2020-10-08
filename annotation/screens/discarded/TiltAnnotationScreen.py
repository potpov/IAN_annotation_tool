from pyface.qt import QtGui

from annotation.actions.Action import SideVolumeSplineResetAction
from annotation.controlpanels.AnnotationControlPanel import AnnotationControlPanel
from annotation.visualization.panorex import CanvasPanorexWidget
from annotation.visualization.sidevolume import CanvasSideVolume
from annotation.core.ArchHandler import ArchHandler


class TiltAnnotationScreen(QtGui.QWidget):
    def __init__(self, parent):
        super(TiltAnnotationScreen, self).__init__()
        self.container = parent
        self.layout = QtGui.QGridLayout(self)
        self.container.loaded.connect(self.show_)

        # panorex
        self.panorex = CanvasPanorexWidget(self, tilted=True)
        self.panorex.set_can_edit_spline(False)
        self.panorex.spline_changed.connect(self.sidevolume_show)
        self.layout.addWidget(self.panorex, 0, 0)

        # side volume
        self.sidevolume = CanvasSideVolume(self)
        self.sidevolume.set_can_edit_spline(False)
        self.layout.addWidget(self.sidevolume, 0, 1)

        # tilted side volume
        self.t_sidevolume = CanvasSideVolume(self, tilted=True)
        self.layout.addWidget(self.t_sidevolume, 0, 2)

        # control panel
        self.panel = AnnotationControlPanel()
        self.panel.pos_changed.connect(self.pos_changed_handler)
        self.panel.flags_changed.connect(self.sidevolume_show)
        self.panel.reset_annotation_clicked.connect(self.reset_annotation_clicked_handler)
        self.panel.acquire_annotation_clicked.connect(self.acquire_annotation_clicked_handler)
        self.layout.addWidget(self.panel, 1, 0)

        self.arch_handler = ArchHandler()
        self.current_pos = 0

    def initialize(self):
        self.panorex.set_img()
        self.sidevolume.set_img()

    def pos_changed_handler(self):
        self.current_pos = self.panel.getPosValue()
        self.show_()

    def reset_annotation_clicked_handler(self):
        self.panel.auto_acquire_annotation.setChecked(False)
        self.arch_handler.annotation_masks.set_mask_spline(self.current_pos, None)
        self.arch_handler.history.add(SideVolumeSplineResetAction(self.current_pos))
        self.sidevolume_show()

    def acquire_annotation_clicked_handler(self):
        self.arch_handler.annotation_masks.get_mask_spline(self.current_pos, from_snake=True)
        self.sidevolume_show()

    def show_(self):
        self.panel.setPosSliderMaximum(len(self.arch_handler.arch.get_arch()) - 1)
        self.panorex.show_(pos=self.current_pos)
        self.sidevolume_show()

    def sidevolume_show(self):
        self.sidevolume.show_(pos=self.current_pos,
                              show_dot=self.panel.show_dot.isChecked(),
                              auto_propagate=False,
                              show_mask_spline=False
                              )
        self.t_sidevolume.show_(pos=self.current_pos,
                                show_dot=self.panel.show_dot.isChecked(),
                                auto_propagate=self.panel.auto_acquire_annotation.isChecked(),
                                show_mask_spline=self.panel.show_mask_spline.isChecked()
                                )
