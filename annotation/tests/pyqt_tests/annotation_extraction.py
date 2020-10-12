import sys
import cv2
import numpy as np
import processing
from pyface.qt import QtGui
from annotation.core.ArchHandler import ArchHandler
from annotation.spline.Spline import Spline
from annotation.utils.image import plot, filter_volume_Z_axis, get_coords_by_label_3D, get_mask_by_label
from annotation.utils.math import get_poly_approx_
from annotation.visualization.archview import ArchView
from annotation.visualization.panorex import CanvasPanorex


class Container(QtGui.QWidget):

    def __init__(self):
        super(Container, self).__init__()

        # dicomdir_path = r"C:\Users\crime\Desktop\alveolar_nerve\dataset\DICOM_ANONIMI\PAZIENTE_7\DICOMDIR"
        dicomdir_path = r"C:\Users\crime\Desktop\alveolar_nerve\dataset\Dataset\PROVA14__1948_05_25_NNTViewer_DICOM\DICOM\PROVA14__19480525_DICOM\DICOMDIR"
        # dicomdir_path = r"C:\Users\crime\Desktop\alveolar_nerve\dataset\Dataset\PROVA13__1966_08_06_NNTViewer_DICOM\DICOM\PROVA13__19660806_DICOM\DICOMDIR"
        self.arch_handler = ArchHandler(dicomdir_path)
        self.selected_slice = 96
        self.arch_handler.compute_initial_state(self.selected_slice, want_side_volume=False)
        self.slice = self.arch_handler.volume[self.selected_slice]

        self.archview = ArchView(self)
        self.panorex = CanvasPanorex(self)
        self.panorex.set_can_edit_spline(False)
        self.set_arch_handler()

        self.extract = QtGui.QPushButton("extract")
        self.extract.clicked.connect(self.find_arch)

        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.archview)
        self.layout.addWidget(self.panorex)
        self.layout.addWidget(self.extract)

        self.show_()

    def find_arch(self):
        self.arch_handler.extract_data_from_gt(debug=True)
        self.show_()

    def set_arch_handler(self):
        self.archview.arch_handler = self.arch_handler
        self.panorex.arch_handler = self.arch_handler

    def show_(self):
        self.archview.show_(self.selected_slice, True)
        self.panorex.show_()


class Window(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setContentsMargins(0, 0, 0, 0)
        self.container = Container()
        self.setCentralWidget(self.container)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    windows = Window()
    windows.show()
    app.exec_()
