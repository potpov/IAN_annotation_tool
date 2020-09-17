from pyface.qt import QtGui

from annotation.actions.Action import TiltedPlanesAnnotationAction, DefaultPlanesAnnotationAction
from annotation.components.Dialog import question, information
from annotation.containers import (
    AnnotationContainer,
    PanorexSplineContainer,
    TiltAnnotationContainer,
    ArchSplineContainer,
    SliceSelectionContainer
)
from annotation.components.Dialog3DPlot import Dialog3DPlot
from annotation.core.ArchHandler import ArchHandler


class Container(QtGui.QWidget):

    def __init__(self, parent):
        super(Container, self).__init__()
        self.layout = QtGui.QGridLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.main_window = parent
        self.view_menu = None

        # widgets
        self.slice_selection = None
        self.asc = None
        self.annotation = None

        # data
        self.arch_handler = None

    def add_view_menu(self):
        if self.view_menu is not None:
            return

        self.view_menu = self.main_window.menubar.addMenu("&View")

        view_volume = QtGui.QAction("&Volume", self)
        view_volume.setShortcut("Ctrl+V")
        view_volume.triggered.connect(
            lambda: self.show_Dialog3DPlot(self.arch_handler.volume,
                                           "Volume"))

        view_gt_volume = QtGui.QAction("&GT volume", self)
        view_gt_volume.triggered.connect(
            lambda: self.show_Dialog3DPlot(self.arch_handler.gt_volume,
                                           "Ground truth"))

        view_gt_delaunay = QtGui.QAction("GT volume (&Delaunay)", self)
        view_gt_delaunay.triggered.connect(
            lambda: self.show_Dialog3DPlot(self.arch_handler.gt_delaunay,
                                           "Ground truth with Delaunay smoothing"))

        view_volume_with_gt = QtGui.QAction("Volume with canal", self)
        view_volume_with_gt.triggered.connect(
            lambda: self.show_Dialog3DPlot(self.arch_handler.get_jaw_with_gt(),
                                           "Volume + Ground truth"))

        view_volume_with_delaunay = QtGui.QAction("Volume with canal (Delaunay)", self)
        view_volume_with_delaunay.triggered.connect(
            lambda: self.show_Dialog3DPlot(self.arch_handler.get_jaw_with_delaunay(),
                                           "Volume + Ground truth with Delaunay smoothing"))

        self.view_menu.addAction(view_volume)
        self.view_menu.addAction(view_gt_volume)
        self.view_menu.addAction(view_gt_delaunay)
        self.view_menu.addAction(view_volume_with_gt)
        self.view_menu.addAction(view_volume_with_delaunay)

    def show_Dialog3DPlot(self, volume, title):
        if volume is None or not volume.any():
            information(self, "Plot", "No volume to show")
        dialog = Dialog3DPlot(self)
        dialog.show(volume)

    def add_SliceSelectionContainer(self):
        self.slice_selection = SliceSelectionContainer(self)
        self.slice_selection.slice_selected.connect(self.show_ArchSplineContainer)
        self.slice_selection.set_arch_handler(self.arch_handler)
        self.slice_selection.initialize()
        self.slice_selection.show_img()
        self.layout.addWidget(self.slice_selection, 0, 0)

    def remove_SliceSelectionContainer(self):
        if self.slice_selection is not None:
            self.layout.removeWidget(self.slice_selection)
            self.slice_selection.deleteLater()
            self.slice_selection = None

    def add_ArchSplineContainer(self):
        self.asc = ArchSplineContainer(self)
        self.asc.spline_selected.connect(self.show_PanorexSplineContainer)
        self.asc.set_arch_handler(self.arch_handler)
        self.asc.initialize()
        self.asc.show_img()
        self.layout.addWidget(self.asc, 0, 0)

    def remove_ArchSplineContainer(self):
        if self.asc is not None:
            self.layout.removeWidget(self.asc)
            self.asc.deleteLater()
            self.asc = None

    def add_PanorexSplineContainer(self):
        self.arch_handler.compute_offsetted_arch(pano_offset=0)
        self.arch_handler.compute_panorexes()
        self.psc = PanorexSplineContainer(self)
        self.psc.panorex_spline_selected.connect(self.show_AnnotationContainer)
        self.psc.set_arch_handler(self.arch_handler)
        self.psc.initialize()
        self.psc.show_img()
        self.layout.addWidget(self.psc, 0, 0)

    def remove_PanorexSplineContainer(self):
        if self.psc is not None:
            self.layout.removeWidget(self.psc)
            self.psc.deleteLater()
            self.psc = None

    def add_AnnotationContainer(self):
        def yes(self):
            self.arch_handler.history.add(TiltedPlanesAnnotationAction())
            self.arch_handler.compute_tilted_side_volume()
            self.annotation = TiltAnnotationContainer(self)

        def no(self):
            self.arch_handler.history.add(DefaultPlanesAnnotationAction())
            self.annotation = AnnotationContainer(self)

        self.arch_handler.compute_offsetted_arch(pano_offset=0)
        self.arch_handler.compute_panorexes()
        self.arch_handler.compute_side_volume_dialog(self.arch_handler.SIDE_VOLUME_SCALE)
        question(self, "Tilted planes",
                 "Would you like to use planes orthogonal to the IAN canal as base for the annotations?",
                 yes_callback=lambda: yes(self), no_callback=lambda: no(self))
        self.annotation.set_arch_handler(self.arch_handler)
        self.annotation.initialize()
        self.annotation.show_img()
        self.layout.addWidget(self.annotation, 0, 0)

    def remove_AnnotationContainer(self):
        if self.annotation is not None:
            self.layout.removeWidget(self.annotation)
            self.annotation.deleteLater()
            self.annotation = None

    def dicomdir_changed(self, dicomdir_path):
        def yes_callback(self):
            self.arch_handler.initalize_attributes(0)
            self.arch_handler.load_state()
            self.add_ArchSplineContainer()

        if self.arch_handler is not None:
            self.arch_handler.__init__(dicomdir_path)
        else:
            self.arch_handler = ArchHandler(dicomdir_path)

        self.add_view_menu()
        self.remove_SliceSelectionContainer()
        self.remove_ArchSplineContainer()
        self.remove_AnnotationContainer()
        if self.arch_handler.is_there_data_to_load():
            question(self, "Load data?", "A save file was found. Do you want to load it?",
                     yes_callback=lambda: yes_callback(self), no_callback=self.add_SliceSelectionContainer)
        else:
            # if there is no data to load, then we start from the first screen
            self.add_SliceSelectionContainer()

    def show_ArchSplineContainer(self, slice):
        self.remove_SliceSelectionContainer()
        self.arch_handler.compute_initial_state_dialog(slice)
        self.add_ArchSplineContainer()

    def show_PanorexSplineContainer(self):
        self.remove_ArchSplineContainer()
        self.add_PanorexSplineContainer()

    def show_AnnotationContainer(self):
        # self.remove_ArchSplineContainer()
        self.remove_PanorexSplineContainer()
        self.add_AnnotationContainer()
