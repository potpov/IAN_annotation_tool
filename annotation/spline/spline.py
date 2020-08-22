import numpy as np
import math
from annotation.spline.catmullrom import CatmullRomChain, CatmullRomSpline
from annotation.utils import get_poly_approx


class Spline():
    def __init__(self, coords: list, num_cp=5):
        """
        Creates a spline (Catmull-Rom)

        Args:
            coords (list of (float, float)): List of points of the curve that we want to parametrize
            num_cp (int): Desired amount of control points
        """
        self.curves = None  # list of curves that form the spline
        self.coords = coords  # curve to start
        self.cp = []  # control points
        self.num_cp = num_cp  # desired amount of control points

        self.compute_cp()
        self.build_spline()

    def update_cp(self, idx, x, y):
        """
        Changes the value of a control point given its index and new (x, y) coordinates.
        Also manages swaps between control points on the x axis.

        Args:
            idx (int): index of the changed control point
            x (float): new x
            y (float): new y

        Returns:
            (int): new index for the changed control point
        """
        new_idx = idx

        if idx - 1 >= 0 and self.cp[idx - 1][0] >= x:
            new_idx = idx - 1
            tmp = self.cp[new_idx]
            self.cp[new_idx] = (x, y)
            self.cp[idx] = tmp
            self.update_curve(new_idx)
            self.update_curve(idx)
        elif idx + 1 < len(self.cp) and self.cp[idx + 1][0] < x:
            new_idx = idx + 1
            tmp = self.cp[new_idx]
            self.cp[new_idx] = (x, y)
            self.cp[idx] = tmp
            self.update_curve(new_idx)
            self.update_curve(idx)
        else:
            self.cp[idx] = (x, y)
            self.update_curve(idx)

        return new_idx

    def compute_cp(self):
        if len(self.coords) == 0:
            return
        self.cp = [self.coords[0], ]
        offset = len(self.coords) // self.num_cp
        self.cp.extend(self.coords[1:-1:offset])
        self.cp.append(self.coords[-1])

    def add_cp(self, x, y):
        """
        Adds a new cp to the spline

        Args:
            x (float): x coordinate
            y (float): y coordinate

        Returns:
            (int): index of the newly added cp
        """
        for pos, (_x, _y) in enumerate(self.cp):
            if x < _x:
                self.cp.insert(pos, (x, y))
                self.build_spline()
                return pos
        self.cp.append((x, y))
        self.build_spline()
        return len(self.cp) - 1

    def remove_cp(self, idx):
        """
        Removes cp from the spline

        Args:
            idx (int): index of the cp to remove
        """
        del self.cp[idx]
        self.build_spline()

    def build_spline(self):
        """
        Uses Catmull Rom algorithm to construct the spline.
        The spline produced is divided in sub-curves by the control points.
        It stores the spline in self.curves.
        """
        self.curves = CatmullRomChain(self.cp)

    def update_curve(self, cp_idx):
        """
        Re-computes self.curves, only updating the 4 sub-curves starting from one cp index.

        Args:
            cp_idx (int): index of the cp around which we need to update the spline
        """
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
        """
        UNUSED function to draw the spline on a numpy array

        Args:
            img (np.ndarray): source gray-scale image

        Returns:
            (np.ndarray): colored image with the arch in red
        """
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
        """
        Returns a polynomial approximation of the spline

        Returns:
            (np.poly1d, float, float): polynomial approximation, minimum x and maximum x
        """
        spline = self.get_spline()
        return get_poly_approx(spline)

    def get_spline(self):
        """
        Returns self.curves as one only list of coordinates

        Returns:
            (list of (float, float)): full spline
        """
        return [point for curve in self.curves for point in curve if not math.isnan(point[0])]

    def get_json(self):
        """
        Returns a summary of the spline

        Returns:
            (dict): summary
        """
        data = {}
        data['num_cp'] = self.num_cp
        data['cp'] = [{'x': float(cp[0]),
                       'y': float(cp[1])}
                      for cp in self.cp]
        return data

    def read_json(self, data, build_spline=True):
        """
        Reads dictionary and loads information on the spline

        Args:
            data (dict): data to load
            build_spline (bool): whether to compute the spline or not
        """
        self.num_cp = data['num_cp']
        self.cp = [(cp['x'], cp['y']) for cp in data['cp']]
        if build_spline:
            self.build_spline()
