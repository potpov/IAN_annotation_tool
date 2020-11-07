from pyface.qt import QtGui
from abc import abstractmethod
from annotation.components.Menu import Menu
from annotation.components.message.Messenger import Messenger
from annotation.core.ArchHandler import ArchHandler
from annotation.utils.metaclasses import AbstractQObjectMeta


class Screen(QtGui.QWidget, metaclass=AbstractQObjectMeta):
    def __init__(self, parent):
        """
        Application screen

        Args:
             parent (annotation.screens.Container.Container): screen container
        """
        super(Screen, self).__init__()
        self.container = parent
        self.arch_handler = ArchHandler()
        self.layout = QtGui.QGridLayout(self)
        self.mb = Menu()
        self.messenger = Messenger()

    def start_(self):
        """
        Sets up the screen.

        This is a template method for a fixed flow of operations.
        """
        self.initialize()
        self.connect_signals()
        self.show_()

    def remove(self):
        """Destroys the screen itself"""
        if type(self.container.screen) == type(self):
            self.container.layout.removeWidget(self)
            self.deleteLater()
            self.container.screen = None

    @abstractmethod
    def next_screen(self):
        """It should call container.transition_to(ScreenClass)"""
        pass

    @abstractmethod
    def connect_signals(self):
        """Here class signals should be connected"""
        pass

    @abstractmethod
    def initialize(self):
        """Do ArchHandler, Menu or other widget function calls to setup the screen and the environment"""
        pass

    @abstractmethod
    def show_(self):
        """Shows the widgets on screen"""
        pass
