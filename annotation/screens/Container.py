from PyQt5 import QtCore
from pyface.qt import QtGui

from annotation.actions.Action import TiltedPlanesAnnotationAction, DefaultPlanesAnnotationAction
from annotation.components.Dialog import question, information, LoadingDialog
from annotation.screens.AnnotationScreen import AnnotationScreen
from annotation.screens.ArchSplineScreen import ArchSplineScreen
from annotation.screens.PanorexSplineScreen import PanorexSplineScreen
from annotation.screens.SliceSelectionScreen import SliceSelectionScreen
from annotation.components.Dialog3DPlot import Dialog3DPlot
from annotation.core.ArchHandler import ArchHandler


class Container(QtGui.QWidget):
    saved = QtCore.pyqtSignal()
    loaded = QtCore.pyqtSignal()

    def __init__(self, parent):
        """
        Screen manager

        Args:
             parent (annotation.containers.Window.Window): main window
        """
        super(Container, self).__init__()
        self.layout = QtGui.QGridLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.window = parent
        self.window.mb.save.connect(self.save)
        self.window.mb.autosave.connect(self.autosave)
        self.window.mb.load.connect(self.load)

        # screens (always register here all screens)
        self.slice_sel = None
        self.arch_spline = None
        self.pano_spline = None
        self.annotation = None

        # data
        self.arch_handler = None

    ###########
    # MENUBAR #
    ###########

    def connect_to_menubar(self):
        # view
        self.window.mb.view_volume.connect(
            lambda: self.show_Dialog3DPlot(self.arch_handler.volume, "Volume"))

        self.window.mb.view_gt_volume.connect(
            # lambda: self.show_Dialog3DPlot(self.arch_handler.gt_volume, "Ground truth"))
            lambda: self.show_Dialog3DPlot(self.arch_handler.get_simpler_gt_volume(), "Ground truth"))

        self.window.mb.view_gt_volume_delaunay.connect(
            lambda: self.show_Dialog3DPlot(self.arch_handler.gt_delaunay, "Ground truth with Delaunay smoothing"))

        self.window.mb.view_volume_with_gt.connect(
            lambda: self.show_Dialog3DPlot(self.arch_handler.get_jaw_with_gt(), "Volume + Ground truth"))

        self.window.mb.view_volume_with_delaunay.connect(
            lambda: self.show_Dialog3DPlot(self.arch_handler.get_jaw_with_delaunay(),
                                           "Volume + Ground truth with Delaunay smoothing"))

        # annotation
        self.window.mb.export_mask_imgs.connect(self.arch_handler.export_annotations_as_imgs)
        self.window.mb.export_annotated_dicom.connect(self.arch_handler.export_annotations_as_dicom)
        self.window.mb.export_gt_volume.connect(self.arch_handler.export_gt_volume)
        self.window.mb.apply_delaunay.connect(self.arch_handler.compute_gt_volume_delaunay)

    def enable_view_menu(self):
        self.window.mb.enable_(self.window.mb.view)

    def enable_annotation_menu(self):
        self.window.mb.enable_(self.window.mb.annotation)

    def disable_annotation_menu(self):
        self.window.mb.disable_(self.window.mb.annotation)

    def enable_save_load(self, enabled):
        self.window.mb.enable_save_load(enabled)

    ###############
    # SAVE | LOAD #
    ###############

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

    #######################
    # ADD / REMOVE SCREEN #
    #######################

    def show_Dialog3DPlot(self, volume, title):
        if volume is None or not volume.any():
            information(self, "Plot", "No volume to show")
        dialog = Dialog3DPlot(self, title)
        dialog.show(volume)

    def add_SliceSelectionScreen(self):
        self.enable_save_load(False)
        self.slice_sel = SliceSelectionScreen(self)
        self.slice_sel.slice_selected.connect(self.show_ArchSplineScreen)
        self.slice_sel.set_arch_handler(self.arch_handler)
        self.slice_sel.initialize()
        self.slice_sel.show_()
        self.layout.addWidget(self.slice_sel, 0, 0)

    def remove_SliceSelectionScreen(self):
        if self.slice_sel is not None:
            self.layout.removeWidget(self.slice_sel)
            self.slice_sel.deleteLater()
            self.slice_sel = None

    def add_ArchSplineScreen(self):
        self.enable_save_load(True)
        self.arch_spline = ArchSplineScreen(self)
        self.arch_spline.spline_selected.connect(self.show_PanorexSplineScreen)
        self.arch_spline.set_arch_handler(self.arch_handler)
        self.arch_spline.initialize()
        self.arch_spline.show_()
        self.layout.addWidget(self.arch_spline, 0, 0)

    def remove_ArchSplineScreen(self):
        if self.arch_spline is not None:
            self.layout.removeWidget(self.arch_spline)
            self.arch_spline.deleteLater()
            self.arch_spline = None

    def add_PanorexSplineScreen(self):
        self.enable_save_load(True)
        self.arch_handler.offset_arch(pano_offset=0)
        self.pano_spline = PanorexSplineScreen(self)
        self.pano_spline.panorex_spline_selected.connect(self.show_AnnotationScreen)
        self.pano_spline.set_arch_handler(self.arch_handler)
        self.pano_spline.initialize()
        self.pano_spline.show_()
        self.layout.addWidget(self.pano_spline, 0, 0)

    def remove_PanorexSplineScreen(self):
        if self.pano_spline is not None:
            self.layout.removeWidget(self.pano_spline)
            self.pano_spline.deleteLater()
            self.pano_spline = None

    def add_AnnotationScreen(self):
        def yes(self):
            self.arch_handler.history.add(TiltedPlanesAnnotationAction())
            self.arch_handler.compute_side_volume(self.arch_handler.SIDE_VOLUME_SCALE, tilted=True)
            self.annotation = AnnotationScreen(self)

        def no(self):
            self.arch_handler.history.add(DefaultPlanesAnnotationAction())
            self.arch_handler.compute_side_volume(self.arch_handler.SIDE_VOLUME_SCALE, tilted=False)
            self.annotation = AnnotationScreen(self)

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

    def remove_AnnotationScreen(self):
        if self.annotation is not None:
            self.layout.removeWidget(self.annotation)
            self.annotation.deleteLater()
            self.annotation = None

    def add_PanorexSplineScreen_w_extraction(self):
        self.enable_save_load(True)
        self.arch_handler.compute_initial_state(96, want_side_volume=False)
        self.arch_handler.extract_data_from_gt()
        self.add_PanorexSplineScreen()

    ########################
    # SHOW SCREEN HANDLERS #
    ########################

    def show_ArchSplineScreen(self, slice):
        self.clear()
        self.arch_handler.compute_initial_state(slice)
        self.add_ArchSplineScreen()

    def show_PanorexSplineScreen(self):
        self.clear()
        self.add_PanorexSplineScreen()

    def show_AnnotationScreen(self):
        self.clear()
        self.add_AnnotationScreen()

    def clear(self):
        self.enable_save_load(False)
        self.disable_annotation_menu()
        self.remove_SliceSelectionScreen()
        self.remove_ArchSplineScreen()
        self.remove_PanorexSplineScreen()
        self.remove_AnnotationScreen()

    ###############
    # MAIN METHOD #
    ###############

    def dicomdir_changed(self, dicomdir_path):

        def ask_load(self):
            def yes(self):
                self.arch_handler.load_state()
                self.add_ArchSplineScreen()

            def no(self):
                self.add_SliceSelectionScreen()

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
                     yes_callback=self.add_PanorexSplineScreen_w_extraction,
                     no_callback=lambda: ask_load(self))
        else:
            ask_load(self)
