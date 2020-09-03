from PyQt5 import QtCore
from pyface.qt import QtGui

from annotation.components.Dialog import LoadingDialog
from annotation.widgets.mayavi_qt import MayaviQWidget


class Dialog3DPlot(QtGui.QDialog):
    def __init__(self, parent, title="Volume plot"):
        super(Dialog3DPlot, self).__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.layout = QtGui.QHBoxLayout(self)
        self.mayavi = MayaviQWidget(self)
        self.layout.addWidget(self.mayavi)

    def show(self, volume=None):
        if volume is None or not volume.any():
            return
        LoadingDialog(lambda: self.mayavi.visualization.plot_volume(volume), "Plotting").exec_()
        super().show()
