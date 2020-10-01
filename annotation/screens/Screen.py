from PyQt5 import QtCore
from pyface.qt import QtGui
from abc import ABCMeta, abstractmethod


class ScreenMeta(type(QtCore.QObject), ABCMeta):
    pass


class Screen(QtGui.QWidget, metaclass=ScreenMeta):
    def __init__(self, parent):
        """
        Application screen

        Args:
             parent (annotation.containers.Container.Container): screen container
        """
        super(Screen, self).__init__()
        self.container = parent
        self.arch_handler = None
        self.layout = QtGui.QGridLayout(self)

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def set_arch_handler(self, arch_handler):
        self.arch_handler = arch_handler

    @abstractmethod
    def show_(self):
        pass
