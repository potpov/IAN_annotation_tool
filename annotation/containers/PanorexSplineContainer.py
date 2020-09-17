from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui

from annotation.visualization.panorex import CanvasPanorexWidget
from annotation.controlpanels import PanorexSplineControlPanel
from annotation.components.Toolbar import Toolbar


class PanorexSplineContainer(QtGui.QWidget):
    panorex_spline_selected = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(PanorexSplineContainer, self).__init__()
        self.container = parent
        self.layout = QtGui.QGridLayout(self)

        # toolbar
        self.toolbar = Toolbar()
        self.toolbar.toolbar_load.connect(self.show_img)
        self.layout.setMenuBar(self.toolbar.bar)

        # panorex
        self.panorex = CanvasPanorexWidget(self)
        # self.panorex.spline_changed.connect(None)
        self.layout.addWidget(self.panorex, 0, 0)

        # control panel
        self.panel = PanorexSplineControlPanel()
        self.panel.pos_changed.connect(self.pos_changed_handler)
        self.layout.addWidget(self.panel, 1, 0)

        # continue button
        self.confirm_button = QtWidgets.QPushButton(self, text="Confirm (C)")
        self.confirm_button.setShortcut("C")
        self.confirm_button.clicked.connect(self.panorex_spline_selected.emit)
        self.layout.addWidget(self.confirm_button, 1, 2)

        self.arch_handler = None
        self.current_pos = 0

    def initialize(self):
        self.panorex.set_img()

    def pos_changed_handler(self):
        self.current_pos = self.panel.getPosValue()
        self.show_img()

    def show_img(self):
        self.panel.setPosSliderMaximum(len(self.arch_handler.offsetted_arch) - 1)
        self.panorex.show_(pos=self.current_pos)

    def set_arch_handler(self, arch_handler):
        self.arch_handler = arch_handler
        self.toolbar.arch_handler = arch_handler
        self.panorex.arch_handler = arch_handler
