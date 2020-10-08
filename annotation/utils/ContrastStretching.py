from annotation.core.ArchHandler import ArchHandler
from annotation.utils.math import clip_range
from annotation.utils.metaclasses import SingletonMeta
import numpy as np


class ContrastStretching(metaclass=SingletonMeta):
    def __init__(self):
        """
        Class that manages contrast stretching in a uniform manner.
        It uses min-max method.
        """
        self.arch_handler = ArchHandler()
        self.min_, self.max_ = self.arch_handler.get_min_max_HU()

    def set_min(self, min_):
        self.min_ = min_

    def set_max(self, max_):
        self.max_ = max_

    def set_range(self, min_, max_):
        if min_ > max_:
            max_, min_ = min_, max_
        self.set_min(min_)
        self.set_max(max_)

    def stretch(self, img):
        min_, max_ = 0., 1.
        l_th = self.arch_handler.convert_HU_to_01(self.min_)
        h_th = self.arch_handler.convert_HU_to_01(self.max_)
        ret = ((img - l_th) * (max_ - min_) / (h_th - l_th)) + min_
        return ret
