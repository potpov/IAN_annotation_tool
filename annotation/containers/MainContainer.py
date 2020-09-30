from PyQt5 import QtCore
from pyface.qt import QtGui

from annotation.actions.Action import TiltedPlanesAnnotationAction, DefaultPlanesAnnotationAction
from annotation.components.Dialog import question, information, LoadingDialog
from annotation.containers.AnnotationContainer import AnnotationContainer
from annotation.containers.ArchSplineContainer import ArchSplineContainer
from annotation.containers.PanorexSplineContainer import PanorexSplineContainer
from annotation.containers.SliceSelectionContainer import SliceSelectionContainer
from annotation.components.Dialog3DPlot import Dialog3DPlot
from annotation.core.ArchHandler import ArchHandler


class Container(QtGui.QWidget):
    saved = QtCore.pyqtSignal()
    loaded = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(Container, self).__init__()
        self.layout = QtGui.QGridLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.main_window = parent
        self.main_window.menubar.save.connect(self.save)
        self.main_window.menubar.autosave.connect(self.autosave)
        self.main_window.menubar.load.connect(self.load)

        # widgets
        self.slice_selection = None
        self.asc = None
        self.psc = None
        self.annotation = None

        # data
        self.arch_handler = None

    def connect_to_menubar(self):
        # view
        self.main_window.menubar.view_volume.connect(
            lambda: self.show_Dialog3DPlot(self.arch_handler.volume, "Volume"))

        self.main_window.menubar.view_gt_volume.connect(
            lambda: self.show_Dialog3DPlot(self.arch_handler.get_simpler_gt_volume(), "Ground truth"))

        self.main_window.menubar.view_gt_volume_delaunay.connect(
            lambda: self.show_Dialog3DPlot(self.arch_handler.gt_delaunay, "Ground truth with Delaunay smoothing"))

        self.main_window.menubar.view_volume_with_gt.connect(
            lambda: self.show_Dialog3DPlot(self.arch_handler.get_jaw_with_gt(), "Volume + Ground truth"))

        self.main_window.menubar.view_volume_with_delaunay.connect(
            lambda: self.show_Dialog3DPlot(self.arch_handler.get_jaw_with_delaunay(),
                                           "Volume + Ground truth with Delaunay smoothing"))

        # annotation
        self.main_window.menubar.export_mask_imgs.connect(self.arch_handler.export_annotations_as_imgs)
        self.main_window.menubar.export_annotated_dicom.connect(self.arch_handler.export_annotations_as_dicom)
        self.main_window.menubar.export_gt_volume.connect(self.arch_handler.export_gt_volume)
        self.main_window.menubar.apply_delaunay.connect(self.arch_handler.compute_gt_volume_delaunay)

    def enable_view_menu(self):
        self.main_window.menubar.enable_(self.main_window.menubar.view)

    def enable_annotation_menu(self):
        self.main_window.menubar.enable_(self.main_window.menubar.annotation)

    def disable_annotation_menu(self):
        self.main_window.menubar.disable_(self.main_window.menubar.annotation)

    def enable_save_load(self, enabled):
        self.main_window.menubar.enable_save_load(enabled)

    def save(self):
        def yes(self):
            self.arch_handler.save_state()
            self.saved.emit()

        if self.arch_handler.is_there_data_to_load():
            message = "Save data was found. Are you sure you want to overwrite the save?"
            question(self, "Save", message, yes_callback=lambda: yes(self))
        else:
            yes(self)

    def autosave(self, autosave):
        self.arch_handler.history.set_autosave(autosave)

    def load(self):
        def yes(self):
            self.arch_handler.load_state()
            self.loaded.emit()

        title = "Load"
        if self.arch_handler.is_there_data_to_load():
            message = "Save data was found. Are you sure you want to discard current changes and load from disk?"
            question(self, title, message, yes_callback=lambda: yes(self), default="no")
        else:
            information(self, title, "Nothing to load.")

    def show_Dialog3DPlot(self, volume, title):
        if volume is None or not volume.any():
            information(self, "Plot", "No volume to show")
        dialog = Dialog3DPlot(self, title)
        dialog.show(volume)

    def add_SliceSelectionContainer(self):
        self.enable_save_load(False)
        self.slice_selection = SliceSelectionContainer(self)
        self.slice_selection.slice_selected.connect(self.show_ArchSplineContainer)
        self.slice_selection.set_arch_handler(self.arch_handler)
        self.slice_selection.initialize()
        self.slice_selection.show_()
        self.layout.addWidget(self.slice_selection, 0, 0)

    def remove_SliceSelectionContainer(self):
        if self.slice_selection is not None:
            self.layout.removeWidget(self.slice_selection)
            self.slice_selection.deleteLater()
            self.slice_selection = None

    def add_ArchSplineContainer(self):
        self.enable_save_load(True)
        self.asc = ArchSplineContainer(self)
        self.asc.spline_selected.connect(self.show_PanorexSplineContainer)
        self.asc.set_arch_handler(self.arch_handler)
        self.asc.initialize()
        self.asc.show_()
        self.layout.addWidget(self.asc, 0, 0)

    def remove_ArchSplineContainer(self):
        if self.asc is not None:
            self.layout.removeWidget(self.asc)
            self.asc.deleteLater()
            self.asc = None

    def add_PanorexSplineContainer(self):
        self.enable_save_load(True)
        self.arch_handler.offset_arch(pano_offset=0)
        self.psc = PanorexSplineContainer(self)
        self.psc.panorex_spline_selected.connect(self.show_AnnotationContainer)
        self.psc.set_arch_handler(self.arch_handler)
        self.psc.initialize()
        self.psc.show_()
        self.layout.addWidget(self.psc, 0, 0)

    def remove_PanorexSplineContainer(self):
        if self.psc is not None:
            self.layout.removeWidget(self.psc)
            self.psc.deleteLater()
            self.psc = None

    def add_AnnotationContainer(self):
        def yes(self):
            self.arch_handler.history.add(TiltedPlanesAnnotationAction())
            self.arch_handler.compute_side_volume(self.arch_handler.SIDE_VOLUME_SCALE, tilted=True)
            self.annotation = AnnotationContainer(self)

        def no(self):
            self.arch_handler.history.add(DefaultPlanesAnnotationAction())
            self.arch_handler.compute_side_volume(self.arch_handler.SIDE_VOLUME_SCALE, tilted=False)
            self.annotation = AnnotationContainer(self)

        self.enable_save_load(True)
        self.enable_annotation_menu()
        self.arch_handler.offset_arch(pano_offset=0)
        title = "Tilted planes"
        if not self.arch_handler.L_canal_spline.is_empty() or not self.arch_handler.R_canal_spline.is_empty():
            message = "Would you like to use planes orthogonal to the IAN canal as base for the annotations?"
            question(self, title, message, yes_callback=lambda: yes(self), no_callback=lambda: no(self), default="no")
        else:
            message = "You will annotate on vertical slices because there are no canal splines."
            information(self, title, message)
            no(self)

        self.annotation.set_arch_handler(self.arch_handler)
        self.annotation.initialize()
        self.annotation.show_()
        self.layout.addWidget(self.annotation, 0, 0)

    def remove_AnnotationContainer(self):
        if self.annotation is not None:
            self.layout.removeWidget(self.annotation)
            self.annotation.deleteLater()
            self.annotation = None

    def add_AnnotationContainer_w_extraction(self):
        self.enable_save_load(True)
        self.arch_handler.compute_initial_state(96, want_side_volume=False)
        self.arch_handler.extract_data_from_gt()
        self.add_AnnotationContainer()

    def dicomdir_changed(self, dicomdir_path):

        def ask_load(self):
            def yes(self):
                self.arch_handler.load_state()
                self.add_ArchSplineContainer()

            def no(self):
                self.add_SliceSelectionContainer()

            if self.arch_handler.is_there_data_to_load():
                question(self, "Load data?", "A save file was found. Do you want to load it?",
                         yes_callback=lambda: yes(self), no_callback=lambda: no(self))
            else:
                no(self)

        if self.arch_handler is not None:
            self.arch_handler.__init__(dicomdir_path)
        else:
            self.arch_handler = ArchHandler(dicomdir_path)
            self.connect_to_menubar()

        self.clear()
        self.enable_view_menu()

        if self.arch_handler.get_simpler_gt_volume().any():
            title = "Ground truth available"
            message = "This DICOM has already annotations available. Would you like to use those as an initialization for the annotation?"
            question(self, title, message,
                     yes_callback=self.add_AnnotationContainer_w_extraction,
                     no_callback=lambda: ask_load(self))
        else:
            ask_load(self)

    def show_ArchSplineContainer(self, slice):
        self.clear()
        self.arch_handler.compute_initial_state(slice)
        self.add_ArchSplineContainer()

    def show_PanorexSplineContainer(self):
        self.clear()
        self.add_PanorexSplineContainer()

    def show_AnnotationContainer(self):
        self.clear()
        self.add_AnnotationContainer()

    def clear(self):
        self.enable_save_load(False)
        self.disable_annotation_menu()
        self.remove_SliceSelectionContainer()
        self.remove_ArchSplineContainer()
        self.remove_PanorexSplineContainer()
        self.remove_AnnotationContainer()
