from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui


class Slider(QtGui.QWidget):
    valueChanged = QtCore.pyqtSignal()

    def __init__(self, orientation, name=None):
        """
        Widget that connects a QSlider and a QSpinBox for better interactions.
        It can also display a tag name and has a "reset to default" button

        Args:
            orientation (int): either Qt.Horizontal or Qt.Vertical
            name (str): tag name
        """
        super(Slider, self).__init__()

        if orientation == QtCore.Qt.Horizontal:
            self.layout = QtGui.QHBoxLayout(self)
        elif orientation == QtCore.Qt.Vertical:
            self.layout = QtGui.QVBoxLayout(self)
        else:
            raise ValueError("Orientation should be either Qt.Horizontal or Qt.Vertical")

        if name:
            self.label = QtWidgets.QLabel(name)
            self.label.setAlignment(QtCore.Qt.AlignCenter)
            self.layout.addWidget(self.label)

        self.default = None

        # widgets
        self.slider = QtWidgets.QSlider(orientation)
        self.box = QtWidgets.QSpinBox()
        self.reset = QtWidgets.QPushButton("Reset")

        # slider settings
        self.slider.valueChanged.connect(self.box.setValue)
        self.slider.valueChanged.connect(self.valueChanged.emit)
        self.slider.rangeChanged.connect(self.box.setRange)

        # box settings
        self.box.setRange(self.slider.minimum(), self.slider.maximum())
        self.box.setFixedWidth(50)
        self.box.valueChanged.connect(self.slider.setValue)

        # reset settings
        self.reset.clicked.connect(self.resetToDefault)

        # layout settings
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.slider)
        self.layout.addWidget(self.box)
        self.layout.addWidget(self.reset)

    def resetToDefault(self):
        if self.default is not None:
            self.box.setValue(self.default)

    ###########
    # Getters #
    ###########

    def value(self):
        return self.slider.value()

    def minimum(self):
        return self.slider.minimum()

    def maximum(self):
        return self.slider.maximum()

    ###########
    # Setters #
    ###########

    def setMinimum(self, val):
        self.slider.setMinimum(val)

    def setMaximum(self, val):
        self.slider.setMaximum(val)

    def setRange(self, minimum, maximum):
        self.slider.setRange(minimum, maximum)

    def setDefaultValue(self, val):
        self.default = val

    def setValue(self, val):
        self.slider.setValue(val)

    def setTickPosition(self, position):
        self.slider.setTickPosition(position)

    def setTickInterval(self, interval):
        self.slider.setTickInterval(interval)

    def setText(self, text):
        self.label.setText(text)
