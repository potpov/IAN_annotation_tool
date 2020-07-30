from PyQt5 import QtCore
from pyface.qt import QtGui

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
        self.slice_selection.set_img(self.arch_handler.volume[96])
        self.layout.addWidget(self.slice_selection, 0, 0)

    def remove_SliceSelectionWidget(self):
        if self.slice_selection is not None:
            self.layout.removeWidget(self.slice_selection)
            self.slice_selection.deleteLater()
            self.slice_selection = None

    def add_ArchPanorexContainerWidget(self):
        self.apc = ArchPanorexContainerWidget(self)
        self.apc.set_arch_handler(self.arch_handler)
        self.apc.initialize()
        self.apc.show_img()
        self.layout.addWidget(self.apc, 0, 0)

    def remove_ArchPanorexContainerWidget(self):
        if self.apc is not None:
            self.layout.removeWidget(self.apc)
            self.apc.deleteLater()
            self.apc = None

    def select_dicomdir(self, dicomdir_path):
        if self.arch_handler is not None:
            self.arch_handler.reset(dicomdir_path)
        else:
            self.arch_handler = ArchHandler(dicomdir_path)

        self.add_SliceSelectionWidget()
        self.remove_ArchPanorexContainerWidget()

        if self.plot3d:
            self.mayavi_widget.visualization.plot_volume(self.arch_handler.volume)

    def show_arch_pano_widget(self, slice):
        self.remove_SliceSelectionWidget()
        self.arch_handler.compute_initial_state(slice)
        self.add_ArchPanorexContainerWidget()
