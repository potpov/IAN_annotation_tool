from Plane import Plane
from annotation.components.Dialog import ProgressLoadingDialog
import numpy as np
import cv2


class SideVolume():
    def __init__(self, arch_handler, scale):
        self.ah = arch_handler
        self.scale = scale
        self.original = None
        self.data = None
        self.update()

    def _postprocess_data(self):
        # rescaling the projection volume properly
        self.original = self.data
        width = int(self.data.shape[2] * self.scale)
        height = int(self.data.shape[1] * self.scale)
        scaled_side_volume = np.ndarray(shape=(self.data.shape[0], height, width))

        for i in range(self.data.shape[0]):
            scaled_side_volume[i] = cv2.resize(self.data[i, :, :], (width, height), interpolation=cv2.INTER_AREA)

        # padding the side volume and rescaling
        scaled_side_volume = cv2.normalize(scaled_side_volume, scaled_side_volume, 0, 1, cv2.NORM_MINMAX)
        self.original = cv2.normalize(self.original, self.original, 0, 1, cv2.NORM_MINMAX)
        self.data = scaled_side_volume

    def __update(self, step_fn=None):
        """
        Computes and updates the side volume.

        Args:
            scale (float): scale of side volume w.r.t. volume dimensions
        """
        self.data = self.ah.line_slice(self.ah.side_coords, step_fn=step_fn)
        self._postprocess_data()

    def update(self):
        pld = ProgressLoadingDialog("Computing side volume")
        pld.set_function(lambda: self.__update(step_fn=pld.get_signal()))
        pld.start()

    def get_slice(self, pos):
        """
        Returns a slice of side volume at position pos

        Args:
            pos (int): position

        Returns:
            (numpy.ndarray): slice of side volume
        """
        if self.data is None:
            return None
        return self.data[pos]

    def get(self):
        """
        Returns side volume

        Returns:
             (numpy.ndarray): side volume
        """
        return self.data


class TiltedSideVolume(SideVolume):
    def __init__(self, arch_handler, scale):
        self.planes = [None] * len(arch_handler.side_coords)
        super().__init__(arch_handler, scale)

    def _compute_on_spline(self, spline, step_fn=None):
        if spline is None:
            return
        p, start, end = spline.get_poly_spline()
        derivative = np.polyder(p, 1)
        for x in range(self.data.shape[0]):
            if x in range(int(start), int(end)):
                step_fn is not None and step_fn(x, self.data.shape[0])
                side_coord = self.ah.side_coords[x]
                plane = Plane(self.ah.Z, len(side_coord))
                plane.from_line(side_coord)
                angle = -np.degrees(np.arctan(derivative(x)))
                plane.tilt_z(angle, p(x))
                cut = self.ah.plane_slice(plane)
                print("cutting x: {}".format(x))
                self.planes[x] = plane
                self.data[x] = cut

    def update(self):
        n = len(self.ah.side_coords)
        h = self.ah.Z
        w = max([len(points) for points in self.ah.side_coords])
        self.data = np.zeros((n, h, w))
        pld = ProgressLoadingDialog("Computing tilted views")
        pld.set_function(lambda: self._compute_on_spline(self.ah.L_canal_spline, step_fn=pld.get_signal()))
        pld.start()
        pld.set_function(lambda: self._compute_on_spline(self.ah.R_canal_spline, step_fn=pld.get_signal()))
        pld.start()
        self._postprocess_data()
