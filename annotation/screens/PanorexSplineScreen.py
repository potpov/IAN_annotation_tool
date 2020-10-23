from PyQt5 import QtWidgets, QtCore
from annotation.controlpanels.SkipControlPanel import SkipControlPanel
from annotation.screens.AnnotationScreen import AnnotationScreen
from annotation.screens.Screen import Screen
from annotation.visualization.archview import ArchView
from annotation.visualization.panorex import CanvasPanorex


class PanorexSplineScreen(Screen):
    panorex_spline_selected = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.container.loaded.connect(self.show_)
        self.current_pos = 0

        # arch view
        self.archview = ArchView(self)
        self.layout.addWidget(self.archview, 0, 0)

        # panorex
        self.panorex = CanvasPanorex(self)
        self.layout.addWidget(self.panorex, 0, 1)

        # sparsity selector
        self.panel = SkipControlPanel()
        self.panel.skip_changed.connect(self.skip_changed_handler)
        self.layout.addWidget(self.panel, 1, 0, 1, 2)

        # continue button
        self.confirm_button = QtWidgets.QPushButton(self, text="Confirm (C)")
        self.confirm_button.setShortcut("C")
        self.confirm_button.clicked.connect(self.panorex_spline_selected.emit)
        self.layout.addWidget(self.confirm_button, 1, 2)

    def initialize(self):
        self.mb.enable_save_load(True)
        self.arch_handler.offset_arch(pano_offset=0)
        self.panorex.set_img()
        max_ = len(self.arch_handler.arch.get_arch()) - 1
        self.panel.setSkipMaximum(max_)
        self.panel.setSkipValue(self.arch_handler.annotation_masks.skip)

    def skip_changed_handler(self, skip):
        self.arch_handler.annotation_masks.set_skip(skip)

    def show_(self):
        self.panorex.show_()
        self.archview.show_(self.arch_handler.selected_slice, True)

    def connect_signals(self):
        self.panorex_spline_selected.connect(self.next_screen)

    def next_screen(self):
        self.container.transition_to(AnnotationScreen)
