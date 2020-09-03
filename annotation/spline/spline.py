import cv2
import numpy as np
from annotation.spline.catmullrom import CatmullRomChain, CatmullRomSpline, CENTRIPETAL
from annotation.utils import get_poly_approx
from functools import reduce
import operator
import math


class Spline():
    def __init__(self, coords, num_cp=0, kind=CENTRIPETAL):
        """
        Class that manages a spline produced with the Catmull-Rom algorithm.

        The spline uses a set of control points ordered on the x axis,
        in order to have only one y for each point in the spline.

        Args:
            coords (list of (float, float)): initial set of coordinates
            num_cp (int): initial desired amount of control points
            kind (float): value between 0 and 1. Common values are UNIFORM (0.0), CENTRIPETAL (0.5) and CHORDAL (1.0)
        """
        self.curves = None  # list of curves that form the spline
        self.coords = coords  # curve to start
        self.cp = []  # control points
        self.num_cp = num_cp  # desired amount of control points
        self.kind = kind
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
        """
        Computes control points.

        It starts from the initial set of coordinates, then extracts self.num_cp control points.
        Finally, adds the first and last point of the set to self.cp
        """
        if len(self.coords) == 0:
            return
        self.cp = [self.coords[0], ]
        offset = int(len(self.coords) / self.num_cp)
        self.cp.extend(self.coords[1:-1:offset])
        self.cp.append(self.coords[-1])
        self.num_cp = len(self.cp)

    def add_cp(self, x, y):
        """
        Adds a new cp to the spline

        Args:
            x (float): x coordinate
            y (float): y coordinate

        Returns:
            (int): index of the newly added cp
        """
        self.num_cp += 1
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
        self.num_cp -= 1
        del self.cp[idx]
        self.build_spline()

    def build_spline(self):
        """
        Uses Catmull Rom algorithm to construct the spline.

        The spline produced is divided in sub-curves by the control points.
        It stores the spline in self.curves.
        """
        self.curves = CatmullRomChain(self.cp, kind=self.kind)

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


class ClosedSpline(Spline):
    def __init__(self, coords, num_cp=0, kind=CENTRIPETAL):
        """
        Class that manages a closed spline produced with the Catmull-Rom algorithm.

        The spline uses a set of control poins in counterclockwise order to make the spline as short as possibile.

        Args:
            coords (list of (float, float)): initial set of coordinates
            num_cp (int): initial desired amount of control points
            kind (float): value between 0 and 1. Common values are UNIFORM (0.0), CENTRIPETAL (0.5) and CHORDAL (1.0)
        """
        super().__init__(coords, num_cp, kind)

    def compute_cp(self):
        """
        Computes control points.

        It starts from the initial set of coordinates, then extracts self.num_cp control points.
        """
        if len(self.coords) == 0:
            return
        offset = int(len(self.coords) / self.num_cp)
        if offset == 0:
            offset = 1
        self.cp.extend(self.coords[1:-1:offset])
        self.num_cp = len(self.cp)

    def update_cp(self, idx, x, y):
        """
        Changes the value of a control point given its index and new (x, y) coordinates.

        Args:
            idx (int): index of the changed control point
            x (float): new x
            y (float): new y

        Returns:
            (int): new index for the changed control point
        """
        self.cp[idx] = (x, y)
        self.update_curve(idx)
        self.build_spline()
        return idx

    def add_cp(self, x, y):
        """
        Adds a new cp to the spline.

        FROM https://stackoverflow.com/questions/51074984/sorting-according-to-clockwise-point-coordinates

        Args:
            x (float): x coordinate
            y (float): y coordinate

        Returns:
            (int): index of the newly added cp
        """
        self.num_cp += 1
        self.cp.append((x, y))
        center = tuple(map(operator.truediv, reduce(lambda x, y: map(operator.add, x, y), self.cp), [len(self.cp)] * 2))
        self.cp = sorted(self.cp, key=lambda pt: (-135 - math.degrees(
            math.atan2(*tuple(map(operator.sub, pt, center))[::-1]))) % 360)
        self.build_spline()
        return len(self.cp) - 1

    def build_spline(self):
        """
        Uses Catmull Rom algorithm to construct the spline.

        The spline produced is divided in sub-curves by the control points.
        It stores the spline in self.curves.
        """
        cp = list.copy(self.cp)
        cp.extend(self.cp[0:3])
        self.curves = CatmullRomChain(cp, kind=self.kind)

    def generate_mask(self, img_shape):
        if len(img_shape) == 3:
            n_channels = img_shape[2]
        else:
            n_channels = 1

        mask = np.zeros(img_shape).astype(np.uint8)

        contour = self.get_spline()
        if len(contour) == 0:
            return mask
        contour = np.asarray(contour).astype(int)

        white_color = (255,) * n_channels
        cv2.drawContours(mask, [contour], -1, white_color, 1, 0)
        cv2.fillPoly(mask, [contour], white_color)
        return mask
