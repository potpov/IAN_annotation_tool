from PyQt5 import QtCore
from pyface.qt import QtGui
from conf import labels as l
from annotation.components.Menu import Menu
from annotation.components.message.Messenger import Messenger
from annotation.screens import Screen
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
        self.messenger = Messenger()

        self.mb = Menu()
        self.mb.save.connect(self.save)
        self.mb.autosave.connect(self.autosave)
        self.mb.load.connect(self.load)

        self.screen: Screen = None

        self.arch_handler: ArchHandler = None

    def transition_to(self, ScreenClass: Screen, w_extraction=False):
        self.clear()
        w_extraction and self.setup_extraction()
        self.screen = ScreenClass(self)
        self.screen.start_()
        self.layout.addWidget(self.screen, 0, 0)

    def setup_extraction(self):
        self.mb.enable_save_load(True)
        self.arch_handler.compute_initial_state(96, want_side_volume=False)
        self.arch_handler.extract_data_from_gt()

    ###########
    # MENUBAR #
    ###########

    def connect_to_menubar(self):
        # view
        self.mb.view_volume.connect(
            lambda: self.show_Dialog3DPlot(self.arch_handler.volume, "Volume"))

        self.mb.view_gt_volume.connect(
            # lambda: self.show_Dialog3DPlot(self.arch_handler.gt_volume, "Ground truth"))
            lambda: self.show_Dialog3DPlot(self.arch_handler.get_gt_volume(labels=[l.CONTOUR, l.INSIDE]),
                                           "Ground truth"))

        self.mb.view_gt_volume_delaunay.connect(
            lambda: self.show_Dialog3DPlot(self.arch_handler.gt_delaunay, "Ground truth with Delaunay smoothing"))

        self.mb.view_volume_with_gt.connect(
            lambda: self.show_Dialog3DPlot(self.arch_handler.get_jaw_with_gt(), "Volume + Ground truth"))

        self.mb.view_volume_with_delaunay.connect(
            lambda: self.show_Dialog3DPlot(self.arch_handler.get_jaw_with_delaunay(),
                                           "Volume + Ground truth with Delaunay smoothing"))

        # annotation
        self.mb.export_mask_imgs.connect(self.arch_handler.export_annotations_as_imgs)
        self.mb.export_annotated_dicom.connect(self.arch_handler.export_annotations_as_dicom)
        self.mb.export_gt_volume.connect(self.arch_handler.export_gt_volume)
        self.mb.apply_delaunay.connect(self.arch_handler.compute_gt_volume_delaunay)

    ###############
    # SAVE | LOAD #
    ###############

    def save(self):
        def yes(self):
            self.arch_handler.save_state()
            self.saved.emit()

        if self.arch_handler.is_there_data_to_load():
            message = "Save data was found. Are you sure you want to overwrite the save?"
            self.messenger.question(title="Save", message=message, yes=lambda: yes(self))
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
            self.messenger.question(title, message, lambda: yes(self), default="no")
        else:
            self.messenger.message(kind="information", title=title, message="Nothing to load")

    #######################
    # ADD / REMOVE SCREEN #
    #######################

    def show_Dialog3DPlot(self, volume, title):
        if volume is None or not volume.any():
            self.messenger.message(kind="information", title="Plot", message="No volume to show")
        dialog = Dialog3DPlot(self, title)
        dialog.show(volume)

    def clear(self):
        self.mb.enable_save_load(False)
        self.mb.disable_(self.mb.annotation)
        if self.screen is not None:
            self.screen.remove()

    ###############
    # MAIN METHOD #
    ###############

    def dicomdir_changed(self, dicomdir_path):

        def ask_load(self):
            def yes(self):
                self.arch_handler.load_state()
                self.transition_to(ArchSplineScreen)

            def no(self):
                self.transition_to(SliceSelectionScreen)

            if self.arch_handler.is_there_data_to_load():
                self.messenger.question(title="Load data?", message="A save file was found. Do you want to load it?",
                                        yes=lambda: yes(self), no=lambda: no(self))
            else:
                no(self)

        if self.arch_handler is not None:
            self.arch_handler.__init__(dicomdir_path)
        else:
            self.arch_handler = ArchHandler(dicomdir_path)
            self.connect_to_menubar()

        self.clear()
        self.mb.enable_(self.mb.view)
        self.mb.enable_(self.mb.options)

        if self.arch_handler.get_gt_volume(labels=[l.CONTOUR, l.INSIDE]).any():
            title = "Ground truth available"
            message = "This DICOM has already annotations available. Would you like to use those as an initialization for the annotation?"
            self.messenger.question(title=title, message=message,
                                    yes=lambda: self.transition_to(PanorexSplineScreen, w_extraction=True),
                                    no=lambda: ask_load(self),
                                    parent=self)
        else:
            ask_load(self)
