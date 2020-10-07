from PyQt5 import QtCore
from pyface.qt import QtGui
from abc import abstractmethod

from annotation.utils.metaclasses import AbstractQObjectMeta


class Screen(QtGui.QWidget, metaclass=AbstractQObjectMeta):
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
        """
        Args:
            arch_handler (annotation.core.ArchHandler.ArchHandler): ah
        """
        self.arch_handler = arch_handler

    @abstractmethod
    def show_(self):
        pass
