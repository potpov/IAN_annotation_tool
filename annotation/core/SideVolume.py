from Plane import Plane
import numpy as np
import cv2
import os
import json

from annotation.components.message.Messenger import Messenger


class SideVolume():
    SIDE_VOLUME_FILENAME = "side_volume.npy"
    SIDE_COORDS_FILENAME = "side_coords.npy"
    COORDS_FILENAME = "coords.npy"
    SAVE_DIRNAME = "side_volume"

    def __init__(self, arch_handler, scale):
        """
        Class that manages side volume

        Args:
            arch_handler (annotation.core.ArchHandler.ArchHandler): arch handler that is parent of this object
            scale (float): scale of the desired side_volume wrt the orginal shape
        """
        self.arch_handler = arch_handler
        self.messenger = Messenger()
        self.scale = scale
        self.original = None
        self.data = None
        self.update()

    def is_there_data_to_load(self):
        """Checks for data to load"""
        base = os.path.dirname(self.arch_handler.dicomdir_path)
        dir = os.path.join(base, self.SAVE_DIRNAME)
        sv = os.path.join(dir, self.SIDE_VOLUME_FILENAME)
        sc = os.path.join(dir, self.SIDE_COORDS_FILENAME)
        co = os.path.join(dir, self.COORDS_FILENAME)
        return os.path.isfile(sv) and os.path.isfile(sc) and os.path.isfile(co)

    def save_(self):
        """Saves important data"""
        base = os.path.dirname(self.arch_handler.dicomdir_path)
        dir = os.path.join(base, self.SAVE_DIRNAME)
        if not os.path.exists(dir):
            os.makedirs(dir)
        np.save(os.path.join(dir, self.SIDE_VOLUME_FILENAME), self.original)
        np.save(os.path.join(dir, self.SIDE_COORDS_FILENAME), self.arch_handler.side_coords)
        np.save(os.path.join(dir, self.COORDS_FILENAME), np.asarray(self.arch_handler.coords))

    def load_(self):
        """Loads data and checks for consistency"""
        base = os.path.dirname(self.arch_handler.dicomdir_path)
        dir = os.path.join(base, self.SAVE_DIRNAME)
        sv = os.path.join(dir, self.SIDE_VOLUME_FILENAME)
        sc = os.path.join(dir, self.SIDE_COORDS_FILENAME)
        co = os.path.join(dir, self.COORDS_FILENAME)
        if not os.path.isfile(sv) or not os.path.isfile(sc) or not os.path.isfile(co):
            msg = "Could not load side volume: one or more of these files is missing ({}, {}, {})".format(
                self.SIDE_VOLUME_FILENAME, self.SIDE_COORDS_FILENAME, self.COORDS_FILENAME)
            print(msg)
            raise FileNotFoundError(msg)
        sv_ = np.load(sv)
        sc_ = np.load(sc)
        co_ = np.load(co, allow_pickle=True)

        if not np.array_equal(sc_, self.arch_handler.side_coords):
            msg = "Loaded side coords do not match with current side coords"
            print(msg)
            raise ValueError(msg)
        self.data = sv_
        self.arch_handler.side_coords = sc_
        self.arch_handler.coords = (co_[0], co_[1], co_[2], co_[3])
        self._postprocess_data()

    def _postprocess_data(self):
        """
        Post-process operations on side volume:
            - rescaling
            - normalization
        """
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
        self.data = self.arch_handler.line_slice(self.arch_handler.side_coords, step_fn=step_fn)
        self._postprocess_data()
        # self.save_()

    def update(self):
        """Computes and updates the side volume."""
        self.messenger.progress_message(message="Computing side volume", func=self.__update, func_args={})

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
    PLANES_FILENAME = "planes.npy"
    CANAL_SPLINES_FILENAME = "canals.json"

    def __init__(self, arch_handler, scale):
        """Class that manages a tilted planes side volume"""
        self.messenger = Messenger()
        self.arch_handler = arch_handler
        self.scale = scale
        self.original = None
        self.data = None
        self.planes = [None] * len(arch_handler.side_coords)
        if self.is_there_data_to_load():
            self.try_load()
        else:
            super().__init__(arch_handler, scale)

    def try_load(self):
        """Tries to load data and checks for consistency errors"""
        try:
            self.load_()
        except Exception as e:
            self.messenger.message("warning", title="Error", message=str(e))
            super().__init__(self.arch_handler, self.scale)

    def is_there_data_to_load(self):
        base = os.path.dirname(self.arch_handler.dicomdir_path)
        dir = os.path.join(base, self.SAVE_DIRNAME)
        p = os.path.join(dir, self.PLANES_FILENAME)
        cs = os.path.join(dir, self.CANAL_SPLINES_FILENAME)
        return os.path.isfile(p) and os.path.isfile(cs) and super().is_there_data_to_load()

    def save_(self):
        super().save_()
        base = os.path.dirname(self.arch_handler.dicomdir_path)
        dir = os.path.join(base, self.SAVE_DIRNAME)

        # planes
        p = os.path.join(dir, self.PLANES_FILENAME)
        n, h, w = self.original.shape
        empty = np.zeros((3, h, w), dtype=np.float64)
        planes = np.repeat(empty[np.newaxis, :, :, :], n, axis=0)
        for i, plane in enumerate(self.planes):
            if plane is None:
                continue
            planes[i] = plane.plane
        np.save(p, planes)

        # canal splines
        cs = os.path.join(dir, self.CANAL_SPLINES_FILENAME)
        splines = {
            "l_canal": self.arch_handler.L_canal_spline.get_json(),
            "r_canal": self.arch_handler.R_canal_spline.get_json()
        }
        with open(cs, "w") as outfile:
            json.dump(splines, outfile)

    def load_(self):
        super().load_()
        base = os.path.dirname(self.arch_handler.dicomdir_path)
        dir = os.path.join(base, self.SAVE_DIRNAME)

        # planes
        p = os.path.join(dir, self.PLANES_FILENAME)
        if not os.path.isfile(p):
            msg = "Could not load tilted side volume: {} is missing".format(self.PLANES_FILENAME)
            print(msg)
            raise FileNotFoundError(msg)
        planes = np.load(p)
        n, _, h, w = planes.shape
        self.planes = []
        for plane in planes:
            if not plane.any():
                self.planes.append(None)
                continue
            plane_obj = Plane(h, w)
            plane_obj.plane = plane
            self.planes.append(plane_obj)

        # splines
        cs = os.path.join(dir, self.CANAL_SPLINES_FILENAME)
        if not os.path.isfile(cs):
            msg = "Could not load canal splines: {} is missing".format(self.CANAL_SPLINES_FILENAME)
            print(msg)
            raise FileNotFoundError(msg)
        with open(cs, "r") as infile:
            splines = json.load(infile)
        L_canal_spline = splines['l_canal']
        R_canal_spline = splines['r_canal']

        if not L_canal_spline == self.arch_handler.L_canal_spline.get_json() or not R_canal_spline == self.arch_handler.R_canal_spline.get_json():
            msg = "Loaded side volume corresponding canal splines do not match with current canals"
            print(msg)
            raise ValueError(msg)

    def _compute_on_spline(self, spline, step_fn=None, debug=False):
        """Computes the tilted images on a give spline (left or right)"""
        if spline is None:
            return
        p, start, end = spline.get_poly_spline()
        derivative = np.polyder(p, 1)
        for x in range(self.data.shape[0]):
            if x in range(int(start), int(end)):
                step_fn is not None and step_fn(x, self.data.shape[0])
                side_coord = self.arch_handler.side_coords[x]
                plane = Plane(self.arch_handler.Z, len(side_coord))
                plane.from_line(side_coord)
                angle = -np.degrees(np.arctan(derivative(x)))
                plane.tilt_z(angle, p(x))
                cut = self.arch_handler.plane_slice(plane)
                debug and print("{}/{}".format(x, len(self.planes)), end='\r')
                self.planes[x] = plane
                self.data[x] = cut

    def update(self):
        n = len(self.arch_handler.side_coords)
        h = self.arch_handler.Z
        w = max([len(points) for points in self.arch_handler.side_coords])
        self.data = np.zeros((n, h, w))
        self.messenger.progress_message(func=self._compute_on_spline,
                                        func_args={'spline': self.arch_handler.L_canal_spline},
                                        message="Computing tilted views (L)")
        self.messenger.progress_message(func=self._compute_on_spline,
                                        func_args={'spline': self.arch_handler.R_canal_spline},
                                        message="Computing tilted views (R)")
        self._postprocess_data()
        self.save_()
