from PyQt5 import QtCore
from pyface.qt import QtGui
from annotation.components.MayaviViewer import MayaviViewer
from annotation.components.message.Messenger import Messenger


class Dialog3DPlot(QtGui.QDialog):

    def __init__(self, parent, title="Plot"):
        """
        Window that contains a 3D plot

        Args:
            parent (pyface.qt.QtGui.QWidget): parent widget
            title (str): window header
        """
        super(Dialog3DPlot, self).__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.layout = QtGui.QHBoxLayout(self)
        self.mayavi = MayaviViewer(self)
        self.layout.addWidget(self.mayavi)
        self.messenger = Messenger()

    def show(self, volume=None):
        """
        Shows the plot

        Args:
            volume (numpy.ndarray): volume to plot
        """
        if volume is None or not volume.any():
            return
        self.messenger.loading_message("Plotting", lambda: self.mayavi.visualization.plot_volume(volume))
        super().show()
