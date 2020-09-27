from pyface.qt import QtGui

from annotation.actions.Action import SideVolumeSplineResetAction
from annotation.controlpanels.AnnotationControlPanel import AnnotationControlPanel
from annotation.visualization.panorex import CanvasPanorexWidget
from annotation.visualization.sidevolume import CanvasSideVolume


class AnnotationContainer(QtGui.QWidget):
    def __init__(self, parent):
        super(AnnotationContainer, self).__init__()
        self.container = parent
        self.container.loaded.connect(self.show_)
        self.layout = QtGui.QGridLayout(self)

        # panorex
        self.panorex = CanvasPanorexWidget(self)
        self.panorex.spline_changed.connect(self.sidevolume_show)
        self.layout.addWidget(self.panorex, 0, 0)

        # side volume
        self.sidevolume = CanvasSideVolume(self)
        self.layout.addWidget(self.sidevolume, 0, 1)

        # control panel
        self.panel = AnnotationControlPanel()
        self.panel.pos_changed.connect(self.pos_changed_handler)
        self.panel.flags_changed.connect(self.sidevolume_show)
        self.panel.reset_annotation_clicked.connect(self.reset_annotation_clicked_handler)
        self.panel.acquire_annotation_clicked.connect(self.acquire_annotation_clicked_handler)
        self.layout.addWidget(self.panel, 1, 0, 1, 2)

        self.arch_handler = None
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
                              auto_propagate=self.panel.auto_acquire_annotation.isChecked(),
                              show_mask_spline=self.panel.show_mask_spline.isChecked()
                              )

    def set_arch_handler(self, arch_handler):
        self.arch_handler = arch_handler
        self.panorex.set_can_edit_spline(not self.arch_handler.tilted())
        self.panorex.arch_handler = arch_handler
        self.sidevolume.arch_handler = arch_handler