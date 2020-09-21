from Plane import Plane
from annotation.components.Dialog import LoadingDialog
from annotation.core.AnnotationMasks import AnnotationMasks
import numpy as np
import cv2


class SideVolume():
    def __init__(self, arch_handler, scale):
        self.ah = arch_handler
        self.scale = scale
        self.data = None
        self.update()

    def _postprocess_data(self):
        # rescaling the projection volume properly
        width = int(self.data.shape[2] * self.scale)
        height = int(self.data.shape[1] * self.scale)
        scaled_side_volume = np.ndarray(shape=(self.data.shape[0], height, width))

        for i in range(self.data.shape[0]):
            scaled_side_volume[i] = cv2.resize(self.data[i, :, :], (width, height), interpolation=cv2.INTER_AREA)

        # padding the side volume and rescaling
        scaled_side_volume = cv2.normalize(scaled_side_volume, scaled_side_volume, 0, 1, cv2.NORM_MINMAX)
        self.data = scaled_side_volume

    def update_(self):
        """
        Computes and updates the side volume.

        Args:
            scale (float): scale of side volume w.r.t. volume dimensions
        """
        self.data = self.ah.line_slice(self.ah.side_coords)
        self._postprocess_data()

    def update(self):
        LoadingDialog(self.update_, "Computing side volume")

    def get_slice(self, pos):
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

    def _compute_on_spline(self, spline):
        if spline is None:
            return
        p, start, end = spline.get_poly_spline()
        derivative = np.polyder(p, 1)
        for x in range(self.data.shape[0]):
            if x in range(int(start), int(end)):
                side_coord = self.ah.side_coords[x]
                plane = Plane(self.ah.Z, len(side_coord))
                plane.from_line(side_coord)
                angle = -np.degrees(np.arctan(derivative(x)))
                plane.tilt_z(angle, p(x))
                cut = self.ah.plane_slice(plane)
                print("cutting x: {}".format(x))
                self.planes[x] = plane
                self.data[x] = cut

    def update_(self):
        n = len(self.ah.side_coords)
        h = self.ah.Z
        w = max([len(points) for points in self.ah.side_coords])
        self.data = np.zeros((n, h, w))
        self._compute_on_spline(self.ah.L_canal_spline)
        self._compute_on_spline(self.ah.R_canal_spline)
        self._postprocess_data()
