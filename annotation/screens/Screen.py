from PyQt5 import QtCore
from pyface.qt import QtGui
from abc import abstractmethod

from annotation.core.ArchHandler import ArchHandler
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
        self.arch_handler = ArchHandler()
        self.layout = QtGui.QGridLayout(self)

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def show_(self):
        pass
