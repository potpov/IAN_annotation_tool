from PyQt5 import QtCore
from pyface.qt import QtGui

from annotation.components.Dialog import question, information
from annotation.containers.annotationcontainer import AnnotationContainerWidget
from annotation.containers.archpanorexcontainer import ArchPanorexContainerWidget
from annotation.containers.dialog3Dplot import Dialog3DPlot
from annotation.widgets.sliceselection import SliceSelectionWidget
from annotation.archhandler import ArchHandler


class Container(QtGui.QWidget):
    dicomdir_changed = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super(Container, self).__init__()
        self.layout = QtGui.QGridLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.main_window = parent
        self.view_menu = None

        # widgets
        self.slice_selection = None
        self.apc = None
        self.annotation = None

        # signal connections
        self.dicomdir_changed.connect(self.select_dicomdir)

        # data
        self.arch_handler = None

    def add_view_menu(self):
        if self.view_menu is not None:
            return

        self.view_menu = self.main_window.menubar.addMenu("&View")

        view_volume = QtGui.QAction("&Volume", self)
        view_volume.setShortcut("Ctrl+V")
        view_volume.triggered.connect(lambda: self.show_Dialog3DPlot(self.arch_handler.volume))

        view_gt_volume = QtGui.QAction("&GT volume", self)
        view_gt_volume.triggered.connect(lambda: self.show_Dialog3DPlot(self.arch_handler.gt_volume))

        view_gt_delaunay = QtGui.QAction("GT volume (&delaunay)", self)
        view_gt_delaunay.triggered.connect(lambda: self.show_Dialog3DPlot(self.arch_handler.gt_delaunay))

        view_volume_with_gt = QtGui.QAction("Volume with canal", self)
        view_volume_with_gt.triggered.connect(lambda: self.show_Dialog3DPlot(self.arch_handler.get_jaw_with_gt()))

        view_volume_with_delaunay = QtGui.QAction("Volume with canal (delaunay)", self)
        view_volume_with_delaunay.triggered.connect(
            lambda: self.show_Dialog3DPlot(self.arch_handler.get_jaw_with_delaunay()))

        self.view_menu.addAction(view_volume)
        self.view_menu.addAction(view_gt_volume)
        self.view_menu.addAction(view_gt_delaunay)
        self.view_menu.addAction(view_volume_with_gt)
        self.view_menu.addAction(view_volume_with_delaunay)

    def show_Dialog3DPlot(self, volume=None):
        if volume is None or not volume.any():
            information(self, "Plot", "No volume to show")
        dialog = Dialog3DPlot(self)
        dialog.show(volume)

    def add_SliceSelectionWidget(self):
        self.slice_selection = SliceSelectionWidget(self)
        self.slice_selection.slice_selected.connect(self.show_arch_pano_widget)
        self.slice_selection.arch_handler = self.arch_handler
        img = self.arch_handler.get_section(96, arch=self.slice_selection.arch_line.isChecked())
        self.slice_selection.set_img(img)
        self.layout.addWidget(self.slice_selection, 0, 0)

    def remove_SliceSelectionWidget(self):
        if self.slice_selection is not None:
            self.layout.removeWidget(self.slice_selection)
            self.slice_selection.deleteLater()
            self.slice_selection = None

    def add_ArchPanorexContainerWidget(self):
        self.apc = ArchPanorexContainerWidget(self)
        self.apc.spline_selected.connect(self.show_annotation_widget)
        self.apc.set_arch_handler(self.arch_handler)
        self.apc.initialize()
        self.apc.show_img()
        self.layout.addWidget(self.apc, 0, 0)

    def remove_ArchPanorexContainerWidget(self):
        if self.apc is not None:
            self.layout.removeWidget(self.apc)
            self.apc.deleteLater()
            self.apc = None

    def add_AnnotationContainerWidget(self):
        self.arch_handler.compute_offsetted_arch(pano_offset=0)
        self.arch_handler.compute_panorexes()
        self.arch_handler.compute_side_volume_dialog(self.arch_handler.SIDE_VOLUME_SCALE)
        self.annotation = AnnotationContainerWidget(self)
        self.annotation.set_arch_handler(self.arch_handler)
        self.annotation.initialize()
        self.annotation.show_img()
        self.layout.addWidget(self.annotation, 0, 0)

    def remove_AnnotationContainerWidget(self):
        if self.annotation is not None:
            self.layout.removeWidget(self.annotation)
            self.annotation.deleteLater()
            self.annotation = None

    def select_dicomdir(self, dicomdir_path):
        def yes_callback(self):
            self.arch_handler.initalize_attributes(0)
            self.arch_handler.load_state()
            self.add_ArchPanorexContainerWidget()

        if self.arch_handler is not None:
            self.arch_handler.__init__(dicomdir_path)
        else:
            self.arch_handler = ArchHandler(dicomdir_path)

        self.add_view_menu()
        self.remove_SliceSelectionWidget()
        self.remove_ArchPanorexContainerWidget()
        self.remove_AnnotationContainerWidget()
        if self.arch_handler.is_there_data_to_load():
            question(self, "Load data?", "A save file was found. Do you want to load it?",
                     yes_callback=lambda: yes_callback(self), no_callback=self.add_SliceSelectionWidget)
        else:
            # if there is no data to load, then we start from the first screen
            self.add_SliceSelectionWidget()

    def show_arch_pano_widget(self, slice):
        self.remove_SliceSelectionWidget()
        self.arch_handler.compute_initial_state_dialog(slice)
        self.add_ArchPanorexContainerWidget()

    def show_annotation_widget(self):
        self.remove_ArchPanorexContainerWidget()
        self.add_AnnotationContainerWidget()
