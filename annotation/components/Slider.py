from PyQt5 import QtWidgets, QtCore
from pyface.qt import QtGui


class Slider(QtGui.QWidget):
    valueChanged = QtCore.pyqtSignal()

    def __init__(self, orientation, name=None, step=1):
        """
        Widget that connects a QSlider and a QSpinBox for better interactions.
        It can also display a tag name and has a "reset to default" button

        Args:
            orientation (int): either Qt.Horizontal or Qt.Vertical
            name (str): tag name
            step (int): how much to increment or decrement slider
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

        # step settings
        self.setStep(step)

        # slider settings
        self.slider.valueChanged.connect(self.slider_valueChanged_handler)
        self.slider.valueChanged.connect(self.valueChanged.emit)
        self.slider.rangeChanged.connect(self.box.setRange)

        # box settings
        self.box.setRange(self.slider.minimum(), self.slider.maximum())
        self.box.setFixedWidth(50)
        self.box.valueChanged.connect(self.box_valueChanged_handler)

        # reset settings
        self.reset.clicked.connect(self.resetToDefault)

        # layout settings
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.slider)
        self.layout.addWidget(self.box)
        self.layout.addWidget(self.reset)

    def resetToDefault(self):
        """Resets the slider and spinbox value to default"""
        if self.default is not None:
            self.box.setValue(self.default)

    def _value_step_fix(self, value):
        step_count = int(value / self.step)
        return step_count * self.step

    def box_valueChanged_handler(self, value):
        """Handler a change in the spinbox and changes the slider as well"""
        if self.step != 1:
            value = self._value_step_fix(value)
            self.box.setValue(value)
        self.slider.setValue(value)

    def slider_valueChanged_handler(self, value):
        """Handler a change in the slider and changes the spinbox as well"""
        if self.step != 1:
            value = self._value_step_fix(value)
            self.slider.setValue(value)
        self.box.setValue(value)

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
        self.box.setValue(val)

    def setTickPosition(self, position):
        self.slider.setTickPosition(position)

    def setTickInterval(self, interval):
        self.slider.setTickInterval(interval)

    def setInverted(self, inverted):
        self.slider.setInvertedAppearance(inverted)
        self.slider.setInvertedControls(inverted)

    def setText(self, text):
        self.label.setText(text)

    def setStep(self, step):
        self.step = step
        self.slider.setSingleStep(self.step)
        self.slider.setPageStep(self.step)
        self.box.setSingleStep(self.step)
