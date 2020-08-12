from pyface.qt import QtGui

from annotation.widgets.annotationcontrolpanel import AnnotationControlPanelWidget
from annotation.widgets.panorex import CanvasPanorexWidget
from annotation.widgets.sidevolume import SideVolume


class AnnotationContainerWidget(QtGui.QWidget):
    def __init__(self, parent):
        super(AnnotationContainerWidget, self).__init__()
        self.container = parent
        self.layout = QtGui.QGridLayout(self)

        # panorex
        self.panorex = CanvasPanorexWidget(self)
        self.layout.addWidget(self.panorex, 0, 0)

        # side volume
        self.sidevolume = SideVolume(self)
        self.layout.addWidget(self.sidevolume, 0, 1)

        # control panel
        self.panel = AnnotationControlPanelWidget()
        self.panel.pos_changed.connect(self.pos_changed_handler)
        self.layout.addWidget(self.panel, 1, 0)

        self.arch_handler = None
        self.current_pos = 0

    def initialize(self):
        self.panorex.set_img()

    def pos_changed_handler(self):
        self.current_pos = self.panel.getPosValue()
        self.show_img()

    def show_img(self):
        self.panel.setPosSliderMaximum(len(self.arch_handler.offsetted_arch) - 1)
        self.panorex.show_panorex(pos=self.current_pos)
        self.sidevolume.show_side_view(pos=self.current_pos)

    def set_arch_handler(self, arch_handler):
        self.arch_handler = arch_handler
        self.panorex.arch_handler = arch_handler
        self.sidevolume.arch_handler = arch_handler
