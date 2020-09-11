from PyQt5 import QtWidgets
from pyface.qt import QtGui

from annotation.actions.Action import SideVolumeSplineResetAction
from annotation.components.Dialog import LoadingDialog
from annotation.containers.dialog3Dplot import Dialog3DPlot
from annotation.utils import numpy2pixmap
from annotation.widgets.annotationcontrolpanel import AnnotationControlPanelWidget
from annotation.widgets.panorex import CanvasPanorexWidgetTilt
from annotation.widgets.sidevolume import CanvasSideVolume
from annotation.widgets.toolbar import Toolbar


class TiltAnnotationContainerWidget(QtGui.QWidget):
    def __init__(self, parent):
        super(TiltAnnotationContainerWidget, self).__init__()
        self.container = parent
        self.layout = QtGui.QGridLayout(self)

        # toolbar
        self.toolbar = Toolbar()
        self.toolbar.toolbar_load.connect(self.show_img)
        self.layout.setMenuBar(self.toolbar.bar)

        # panorex
        self.panorex = CanvasPanorexWidgetTilt(self)
        self.panorex.spline_changed.connect(self.sidevolume_show)
        self.layout.addWidget(self.panorex, 0, 0)

        # side volume
        self.sidevolume = CanvasSideVolume(self)
        self.layout.addWidget(self.sidevolume, 0, 1)
        self.t_side_volume = QtWidgets.QLabel(self)
        self.layout.addWidget(self.t_side_volume, 0, 2)

        # update tilted side volume
        self.button = QtGui.QPushButton("update tilted")
        self.button.clicked.connect(self.update_tilted_side_volume)
        self.layout.addWidget(self.button, 1, 2)

        # control panel
        self.panel = AnnotationControlPanelWidget()
        self.panel.pos_changed.connect(self.pos_changed_handler)
        self.panel.flags_changed.connect(self.sidevolume_show)
        self.panel.reset_annotation_clicked.connect(self.reset_annotation_clicked_handler)
        self.panel.acquire_annotation_clicked.connect(self.acquire_annotation_clicked_handler)
        self.panel.show_result_clicked.connect(self.show_result_clicked_handler)
        self.panel.export_mask_imgs_clicked.connect(self.export_mask_imgs_clicked_handler)
        self.layout.addWidget(self.panel, 1, 0)

        self.arch_handler = None
        self.current_pos = 0

    def initialize(self):
        self.panorex.set_img()
        self.sidevolume.set_img()

    def update_tilted_side_volume(self):
        self.arch_handler.compute_tilted_side_volume(self.arch_handler.L_canal_spline)

    def pos_changed_handler(self):
        self.current_pos = self.panel.getPosValue()
        self.show_img()

    def reset_annotation_clicked_handler(self):
        self.panel.auto_acquire_annotation.setChecked(False)
        self.arch_handler.annotation_masks.set_mask_spline(self.current_pos, None)
        self.arch_handler.history.add(SideVolumeSplineResetAction(self.current_pos), debug=True)
        self.sidevolume_show()

    def acquire_annotation_clicked_handler(self):
        self.arch_handler.annotation_masks.get_mask_spline(self.current_pos, from_snake=True)
        self.sidevolume_show()

    def show_result_clicked_handler(self):
        self.arch_handler.extract_annotations()
        dialog = Dialog3DPlot(self, "Volume with annotations")
        dialog.show(self.arch_handler.get_jaw_with_delaunay())

    def export_mask_imgs_clicked_handler(self):
        LoadingDialog(self.arch_handler.annotation_masks.export_mask_imgs, "Exporting mask images").exec_()

    def show_img(self):
        self.panel.setPosSliderMaximum(len(self.arch_handler.offsetted_arch) - 1)
        self.panorex.show_(pos=self.current_pos)
        self.sidevolume_show()

    def sidevolume_show(self):
        self.sidevolume.show_(pos=self.current_pos,
                              show_dot=self.panel.show_dot.isChecked(),
                              show_hint=self.panel.show_hint.isChecked(),
                              auto_propagate=self.panel.auto_acquire_annotation.isChecked(),
                              show_mask_spline=self.panel.show_mask_spline.isChecked()
                              )
        if self.arch_handler.t_side_volume is not None:
            self.t_side_volume.setPixmap(numpy2pixmap(self.arch_handler.t_side_volume[self.current_pos]))
            self.t_side_volume.update()

    def set_arch_handler(self, arch_handler):
        self.arch_handler = arch_handler
        self.toolbar.arch_handler = arch_handler
        self.panorex.arch_handler = arch_handler
        self.sidevolume.arch_handler = arch_handler
