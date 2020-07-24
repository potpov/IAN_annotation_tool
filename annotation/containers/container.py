from PyQt5 import QtCore
from pyface.qt import QtGui

from annotation.containers.archpanorexcontainer import ArchPanorexContainerWidget
from annotation.widgets.sliceselection import SliceSelectionWidget
# from annotation.widgets.test_spline import SliceSelectionWidget
from annotation.widgets.mayavi_qt import MayaviQWidget
from annotation.archhandler import ArchHandler


class Container(QtGui.QWidget):
    dicomdir_changed = QtCore.pyqtSignal(str)
    dicomdir_loaded = QtCore.pyqtSignal()
    slice_selected = QtCore.pyqtSignal(int)

    def __init__(self, plot3d=False):
        super(Container, self).__init__()
        self.layout = QtGui.QGridLayout(self)

        self.slice_selection = SliceSelectionWidget(self)
        self.apc = ArchPanorexContainerWidget(self)

        self.dicomdir_changed.connect(self.select_dicomdir)
        self.dicomdir_loaded.connect(self.show_dicom_slice_widget)
        self.slice_selected.connect(self.show_arch_pano_widget)

        self.volume = None
        self.arch_handler = None

        self.plot3d = plot3d
        if self.plot3d:
            self.mayavi_widget = MayaviQWidget(self)
            self.layout.addWidget(self.mayavi_widget, 0, 1)

    def select_dicomdir(self, dicomdir_path):
        if self.arch_handler is not None:
            self.arch_handler.reset(dicomdir_path)
        else:
            self.arch_handler = ArchHandler(dicomdir_path)
        self.slice_selection.arch_handler = self.arch_handler
        self.apc.set_arch_handler(self.arch_handler)
        self.apc.setParent(None)
        if self.plot3d:
            self.mayavi_widget.visualization.plot_volume(self.volume)
        self.dicomdir_loaded.emit()

    def show_dicom_slice_widget(self):
        self.slice_selection.set_img(self.arch_handler.volume[96])
        self.layout.addWidget(self.slice_selection, 0, 0)

    def show_arch_pano_widget(self, slice):
        self.slice_selection.setParent(None)
        self.arch_handler.compute_initial_state(slice)
        self.apc.initialize()
        self.apc.show_img()
        self.layout.addWidget(self.apc, 0, 2)
