from PyQt5 import QtCore
from pyface.qt import QtGui

from annotation.containers.annotationcontainer import AnnotationContainerWidget
from annotation.containers.archpanorexcontainer import ArchPanorexContainerWidget
from annotation.widgets.sliceselection import SliceSelectionWidget
from annotation.widgets.mayavi_qt import MayaviQWidget
from annotation.archhandler import ArchHandler


class Container(QtGui.QWidget):
    dicomdir_changed = QtCore.pyqtSignal(str)

    def __init__(self, parent, plot3d=False):
        super(Container, self).__init__()
        self.layout = QtGui.QGridLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.main_window = parent

        # widgets
        self.slice_selection = None
        self.apc = None
        self.annotation = None

        self.plot3d = plot3d
        if self.plot3d:
            self.mayavi_widget = MayaviQWidget(self)
            self.layout.addWidget(self.mayavi_widget, 0, 1)

        # signal connections
        self.dicomdir_changed.connect(self.select_dicomdir)

        # data
        self.arch_handler = None

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
        self.arch_handler.compute_side_volume_dialog()
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
        if self.arch_handler is not None:
            self.arch_handler.reset(dicomdir_path)
        else:
            self.arch_handler = ArchHandler(dicomdir_path)
        self.add_SliceSelectionWidget()
        self.remove_ArchPanorexContainerWidget()
        self.remove_AnnotationContainerWidget()

        if self.plot3d:
            self.mayavi_widget.visualization.plot_volume(self.arch_handler.volume)

    def show_arch_pano_widget(self, slice):
        self.remove_SliceSelectionWidget()
        self.arch_handler.compute_initial_state_dialog(slice)
        self.add_ArchPanorexContainerWidget()

    def show_annotation_widget(self):
        self.remove_ArchPanorexContainerWidget()
        self.add_AnnotationContainerWidget()
