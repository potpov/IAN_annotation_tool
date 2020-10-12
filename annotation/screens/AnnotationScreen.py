from PyQt5 import QtCore

from annotation.actions.Action import SideVolumeSplineResetAction
from annotation.screens.Screen import Screen
from annotation.controlpanels.AnnotationControlPanel import AnnotationControlPanel
from annotation.visualization.panorex import CanvasPanorex
from annotation.visualization.sidevolume import CanvasSideVolume


class AnnotationScreen(Screen):
    def __init__(self, parent):
        super().__init__(parent)
        self.container.loaded.connect(self.show_)
        self.current_pos = 0

        self.layout.setAlignment(QtCore.Qt.AlignCenter)

        # panorex
        self.panorex = CanvasPanorex(self)
        self.panorex.spline_changed.connect(self._sidevolume_show)
        self.layout.addWidget(self.panorex, 0, 0)

        # side volume
        self.sidevolume = CanvasSideVolume(self)
        self.layout.addWidget(self.sidevolume, 0, 1, 2, 1)

        # control panel
        self.panel = AnnotationControlPanel()
        self.panel.pos_changed.connect(self.pos_changed_handler)
        self.panel.flags_changed.connect(self._sidevolume_show)
        self.panel.reset_annotation_clicked.connect(self.reset_annotation_clicked_handler)
        self.panel.acquire_annotation_clicked.connect(self.acquire_annotation_clicked_handler)
        self.layout.addWidget(self.panel, 1, 0)

    def initialize(self):
        self.panorex.set_img()
        self.panorex.set_can_edit_spline(not self.arch_handler.tilted())
        self.sidevolume.set_img()

    def pos_changed_handler(self):
        self.arch_handler.history.save_()
        self.arch_handler.annotation_masks.save_mask_splines()
        self.current_pos = self.panel.getPosValue()
        self.show_()

    def reset_annotation_clicked_handler(self):
        self.panel.auto_acquire_annotation.setChecked(False)
        self.arch_handler.annotation_masks.set_mask_spline(self.current_pos, None)
        self.arch_handler.history.add(SideVolumeSplineResetAction(self.current_pos))
        self._sidevolume_show()

    def acquire_annotation_clicked_handler(self):
        self.arch_handler.annotation_masks.get_mask_spline(self.current_pos, from_snake=True)
        self._sidevolume_show()

    def show_(self):
        self.panel.setPosSliderMaximum(len(self.arch_handler.arch.get_arch()) - 1)
        self.panel.setStep(self.arch_handler.annotation_masks.skip + 1)
        self.panorex.show_(pos=self.current_pos)
        self._sidevolume_show()

    def _sidevolume_show(self):
        self.sidevolume.show_(pos=self.current_pos,
                              show_dot=self.panel.show_dot.isChecked(),
                              auto_propagate=self.panel.auto_acquire_annotation.isChecked(),
                              show_mask_spline=self.panel.show_mask_spline.isChecked(),
                              show_cp_boxes=self.panel.show_cp_boxes.isChecked(),
                              )
