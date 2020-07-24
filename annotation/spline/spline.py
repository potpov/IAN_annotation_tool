import numpy as np

from annotation.spline.catmullrom import CatmullRomChain, CatmullRomSpline
from annotation.utils import get_poly_approx


class Spline():
    def __init__(self, coords: list, num_cp=5):
        """
        Creates a spline (Catmull-Rom)

        :param coords: List of points of the curve that we want to parametrize
        :param num_cp: Desired amount of control points
        """
        self.curves = None  # list of curves that form the spline
        self.coords = coords  # curve to start
        self.cp = []  # control points
        self.num_cp = num_cp  # desired amount of control points

        self.compute_cp()
        self.build_spline()

    def set_cp(self, idx, x, y):
        self.cp[idx] = (x, y)
        self.update_curve(idx)

    def compute_cp(self):
        self.cp = [self.coords[0], ]
        offset = len(self.coords) // self.num_cp
        self.cp.extend(self.coords[1:-1:offset])
        self.cp.append(self.coords[-1])

    def build_spline(self):
        self.curves = CatmullRomChain(self.cp)

    def update_curve(self, cp_idx):
        min_curve_idx = max(0, cp_idx - 3)
        max_curve_idx = min(cp_idx, len(self.cp) - 4)
        '''
        (0)   (1)---(2)---(3)---(4)---(5)   (6)
                  0     1     2     3

        cp_idx affects curves with id in range [cp_idx - 3, cp_idx] extrema included
        because:
        len(cp) = len(curves) + 3
        '''
        for curve_idx in range(min_curve_idx, max_curve_idx + 1):  # remember that in range() the max value is excluded
            new_curve = CatmullRomSpline(self.cp[curve_idx],
                                         self.cp[curve_idx + 1],
                                         self.cp[curve_idx + 2],
                                         self.cp[curve_idx + 3])
            self.curves[curve_idx] = new_curve

    def draw_curve(self, img):
        arch_rgb = np.tile(img, (3, 1, 1))
        arch_rgb = np.moveaxis(arch_rgb, 0, -1)
        curve = self.get_spline()
        for i in range(len(curve)):
            x = int(curve[i][1])
            y = int(curve[i][0])
            arch_rgb[x, y] = (1, 0, 0)
            if (y, x) in self.cp:
                arch_rgb[x, y] = (0, 1, 0)
        return arch_rgb

    def get_poly_spline(self):
        spline = self.get_spline()
        return get_poly_approx(spline)

    def get_spline(self):
        return [point for curve in self.curves for point in curve]
