from PyQt5 import QtCore
from pyface.qt import QtGui

from annotation.components.DialogImageSettings import DialogImageSettings


class Menu(QtGui.QWidget):
    # file
    open = QtCore.pyqtSignal()
    save = QtCore.pyqtSignal()
    autosave = QtCore.pyqtSignal(bool)
    load = QtCore.pyqtSignal()

    # view
    view_volume = QtCore.pyqtSignal()
    view_gt_volume = QtCore.pyqtSignal()
    view_gt_volume_delaunay = QtCore.pyqtSignal()
    view_volume_with_gt = QtCore.pyqtSignal()
    view_volume_with_delaunay = QtCore.pyqtSignal()

    # annotation
    export_mask_imgs = QtCore.pyqtSignal()
    export_annotated_dicom = QtCore.pyqtSignal()
    export_gt_volume = QtCore.pyqtSignal()
    apply_delaunay = QtCore.pyqtSignal()

    def __init__(self, window):
        super(Menu, self).__init__(window)
        self.bar = window.menuBar()

        # menus
        self.file = None
        self.view = None
        self.annotation = None
        self.options = None

        self.save_action = None
        self.autosave_action = None
        self.load_action = None

        self.add_menu_file()
        self.add_menu_view()
        self.add_menu_annotation()
        self.add_menu_options()

        self.disable_(self.view)
        self.disable_(self.annotation)

    def get(self):
        return self.bar

    def add_menu_file(self):
        self.file = self.bar.addMenu("&File")
        self.add_action_open()
        self.add_action_save()
        self.add_action_autosave()
        self.add_action_load()
        self.enable_save_load(False)

    def add_menu_view(self):
        if self.view is not None:
            self.enable_(self.view)
            return

        self.view = self.bar.addMenu("&View")

        view_volume_action = QtGui.QAction("&Volume", self)
        view_volume_action.triggered.connect(self.view_volume.emit)
        self.view.addAction(view_volume_action)

        view_gt_volume_action = QtGui.QAction("&GT volume", self)
        view_gt_volume_action.triggered.connect(self.view_gt_volume.emit)
        self.view.addAction(view_gt_volume_action)

        view_gt_volume_delaunay_action = QtGui.QAction("GT volume (&Delaunay)", self)
        view_gt_volume_delaunay_action.triggered.connect(self.view_gt_volume_delaunay.emit)
        self.view.addAction(view_gt_volume_delaunay_action)

        view_volume_with_gt_action = QtGui.QAction("Volume with &canal", self)
        view_volume_with_gt_action.triggered.connect(self.view_volume_with_gt.emit)
        self.view.addAction(view_volume_with_gt_action)

        view_volume_with_delaunay_action = QtGui.QAction("Volume with canal (D&elaunay)", self)
        view_volume_with_delaunay_action.triggered.connect(self.view_volume_with_delaunay.emit)
        self.view.addAction(view_volume_with_delaunay_action)

    def add_action_open(self):
        open_action = QtGui.QAction("&Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open.emit)
        self.file.addAction(open_action)

    def enable_save_load(self, enabled):
        self.save_action.setDisabled(not enabled)
        self.autosave_action.setDisabled(not enabled)
        self.load_action.setDisabled(not enabled)

    def add_action_save(self):
        self.save_action = QtGui.QAction("&Save", self)
        self.save_action.setDisabled(True)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save.emit)
        self.file.addAction(self.save_action)

    def add_action_autosave(self):
        self.autosave_action = QtGui.QAction("Auto-save", self)
        self.autosave_action.setCheckable(True)
        self.autosave_action.setDisabled(True)
        self.autosave_action.triggered.connect(lambda: self.autosave.emit(self.autosave_action.isChecked()))
        self.file.addAction(self.autosave_action)

    def add_action_load(self):
        self.load_action = QtGui.QAction("&Load", self)
        self.load_action.setDisabled(True)
        self.load_action.setShortcut("Ctrl+L")
        self.load_action.triggered.connect(self.load.emit)
        self.file.addAction(self.load_action)

    def add_menu_annotation(self):
        if self.annotation is not None:
            self.enable_(self.annotation)
            return

        self.annotation = self.bar.addMenu("&Annotation")

        export_mask_imgs_action = QtGui.QAction("Export &mask images", self)
        export_mask_imgs_action.triggered.connect(self.export_mask_imgs.emit)
        self.annotation.addAction(export_mask_imgs_action)

        export_annotated_dicom_action = QtGui.QAction("Export &annotated DICOM", self)
        export_annotated_dicom_action.triggered.connect(self.export_annotated_dicom.emit)
        self.annotation.addAction(export_annotated_dicom_action)

        export_gt_volume_action = QtGui.QAction("Export &ground truth volume", self)
        export_gt_volume_action.triggered.connect(self.export_gt_volume.emit)
        self.annotation.addAction(export_gt_volume_action)

        apply_delaunay_action = QtGui.QAction("Apply &Delaunay", self)
        apply_delaunay_action.triggered.connect(self.apply_delaunay.emit)
        self.annotation.addAction(apply_delaunay_action)

    def add_menu_options(self):
        self.options = self.bar.addMenu("&Options")

        image_settings_action = QtGui.QAction("Edit image settings", self)
        image_settings_action.triggered.connect(self.show_options)
        self.options.addAction(image_settings_action)

    def show_options(self):
        DialogImageSettings().exec_()

    def disable_(self, menu):
        menu.setDisabled(True)

    def enable_(self, menu):
        menu.setDisabled(False)
