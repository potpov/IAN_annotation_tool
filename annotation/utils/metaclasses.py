from abc import ABCMeta
from PyQt5 import QtCore


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class QObjectSingletonMeta(type(QtCore.QObject), SingletonMeta):
    pass


class AbstractQObjectMeta(type(QtCore.QObject), ABCMeta):
    pass
