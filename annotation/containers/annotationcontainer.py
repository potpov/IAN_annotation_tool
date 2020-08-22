from pyface.qt import QtGui

from annotation.widgets.annotationcontrolpanel import AnnotationControlPanelWidget
from annotation.widgets.panorex import CanvasPanorexWidget
from annotation.widgets.sidevolume import CanvasSideVolume
from annotation.widgets.toolbar import Toolbar


class AnnotationContainerWidget(QtGui.QWidget):
    def __init__(self, parent):
        super(AnnotationContainerWidget, self).__init__()
        self.container = parent
        self.layout = QtGui.QGridLayout(self)

        # toolbar
        self.toolbar = Toolbar()
        self.toolbar.toolbar_load.connect(self.show_img)
        self.layout.setMenuBar(self.toolbar.bar)

        # panorex
        self.panorex = CanvasPanorexWidget(self)
        self.panorex.spline_changed.connect(
            lambda: self.sidevolume.show_(self.current_pos, self.panel.show_dot.isChecked()))
        self.layout.addWidget(self.panorex, 0, 0)

        # side volume
        self.sidevolume = CanvasSideVolume(self)
        self.layout.addWidget(self.sidevolume, 0, 1)

        # control panel
        self.panel = AnnotationControlPanelWidget()
        self.panel.pos_changed.connect(self.pos_changed_handler)
        self.layout.addWidget(self.panel, 1, 0)

        self.arch_handler = None
        self.current_pos = 0

    def initialize(self):
        self.panorex.set_img()
        self.sidevolume.set_img()

    def pos_changed_handler(self):
        self.current_pos = self.panel.getPosValue()
        self.show_img()

    def show_img(self):
        self.panel.setPosSliderMaximum(len(self.arch_handler.offsetted_arch) - 1)
        self.panorex.show_(pos=self.current_pos)
        self.sidevolume.show_(pos=self.current_pos, show_dot=self.panel.show_dot.isChecked())

    def set_arch_handler(self, arch_handler):
        self.arch_handler = arch_handler
        self.toolbar.arch_handler = arch_handler
        self.panorex.arch_handler = arch_handler
        self.sidevolume.arch_handler = arch_handler
