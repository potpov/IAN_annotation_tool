import os

import numpy as np
import cv2
import json

import processing
from Jaw import Jaw
from annotation.actions.Action import SliceChangedAction
from annotation.actions.History import History
from annotation.spline.spline import Spline
from annotation.utils import get_poly_approx, apply_offset_to_arch


class ArchHandler(Jaw):
    LH_OFFSET = 50
    DUMP_FILENAME = 'dump.json'

    def __init__(self, dicomdir_path):
        """
        Class that handles the arch and panorex computing on top of the Jaw class.

        Args:
            dicomdir_path (str): path of the DICOMDIR file

        Attributes:
            dicomdir_path (str): path of the DICOMDIR file
            history (History): History object that memorizes user changes
            selected_slice (int): index of the selected slice of the volume
            arch_detections (list): list of tuples of each arch of each slice of the volume
            coords (list, list, list, list): (l_offset, coords, h_offset, derivative) tuple of the arch for the selected slice of the volume
            spline (Spline): object that models the arch as a Catmull-Rom spline
            panorex (np.ndarray): panorex computed on one set of coordinates
            LHpanorexes (np.ndarray, np.ndarray): (l_panorex, h_panorex) tuple of panorexes offsetted from the main one
            offsetted_arch (list): coordinates of the main arch offsetted by "offsetted_arch_amount"
            offsetted_arch_amount (int): value between -LH_OFFSET and LH_OFFSET of the coords of the arch for the panorex
            side_coords (list): coordinates of the points that define "side_volume" perimeter
            side_volume (list): volume of the side views of the jaw volume through the two coords arches
        """
        self.reset(dicomdir_path)

    def reset(self, dicomdir_path):
        """
        Resets current ArchHandler object

        Args:
            dicomdir_path (str): path of the DICOMDIR file
        """
        super().__init__(dicomdir_path)
        self.dicomdir_path = dicomdir_path
        self.history = History()
        self.selected_slice = None
        self.arch_detections = None
        self.coords = None
        self.spline = None
        self.panorex = None
        self.LHpanorexes = None
        self.offsetted_arch = None
        self.offsetted_arch_amount = 0
        self.side_coords = None
        self.side_volume = None
        self.compute_arch()

    def compute_arch(self):
        """
        Computes the arch for each slice of the jaw volume.
        """
        self.arch_detections = []
        for i, section in enumerate(self.volume):
            try:
                p, start, end = processing.arch_detection(section)
                self.arch_detections.append((p, start, end))
            except:
                self.arch_detections.append(None)

    def save_state(self):
        data = {}
        data['version'] = 1.0
        data['spline'] = self.spline.get_json()
        data['selected_slice'] = self.selected_slice
        data['history'] = self.history.dump()
        with open(os.path.join(os.path.dirname(self.dicomdir_path), self.DUMP_FILENAME), "w") as outfile:
            json.dump(data, outfile)
        print("saved")

    def load_state(self):
        path = os.path.join(os.path.dirname(self.dicomdir_path), self.DUMP_FILENAME)
        if not os.path.isfile(path):
            print("Nothing to load")
            return

        with open(path, "r") as infile:
            data = json.load(infile)
            self.spline.read_json(data['spline'], build_spline=True)
            self.selected_slice = data['selected_slice']
            self.history.load(data['history'])

        print("loaded")

    def compute_initial_state(self, selected_slice):
        """
        Sets class attributes after the selection of the slice.

        Args:
            selected_slice (int): index of the selected slice in the jaw volume
        """
        self.selected_slice = selected_slice
        self.history.add(SliceChangedAction(selected_slice))
        p, start, end = self.arch_detections[selected_slice]
        l_offset, coords, h_offset, derivative = processing.arch_lines(p, start, end, offset=self.LH_OFFSET)
        self.coords = (l_offset, coords, h_offset, derivative)
        self.spline = Spline(coords, 10)
        self.update_coords()
        self.offsetted_arch = self.spline.get_spline()

        self.compute_panorexes(coords=self.offsetted_arch)
        self.compute_side_coords()
        self.compute_side_volume()

    def update_coords(self):
        """
        Updates the current arch after the changes in the spline.
        Also updates the offsetted arches.
        """
        p, start, end = self.spline.get_poly_spline()
        self.arch_detections[self.selected_slice] = (p, start, end)
        self.coords = processing.arch_lines(p, start, end, offset=self.LH_OFFSET)

    def compute_offsetted_arch(self, offset_amount=0, p=None):
        """
        Computes the offsetted coordinates of an arch, starting from its polynomial approximation.

        Args:
            offset_amount (int): how much to displace the curve
            p (np.poly1d): polynomial approximation of the arch

        Returns:
            list of (float, float): list of xy coordinates of the new offsetted arch
        """
        _, coords, _, _ = self.coords

        if offset_amount == 0 or offset_amount is None:
            self.offsetted_arch_amount = 0
            self.offsetted_arch = coords
            return coords

        if p is None:
            p, _, _ = self.arch_detections[self.selected_slice]

        new_offset = apply_offset_to_arch(coords, offset_amount, p)
        self.offsetted_arch_amount = offset_amount
        self.offsetted_arch = new_offset

    def compute_panorexes(self, coords=None, arch_offset=1):
        """
        Computes and updates panorex and LHpanorexes, given a new set of coordinates.
        If not specified, it uses the class ones.

        Args:
            coords (list of (float, float)): coordinates to use for panorex
            arch_offset (int): coords of the lateral panorexes from the main one
        """
        if coords is None:
            coords = self.coords[1]
            p, start, end = self.arch_detections[self.selected_slice]
        else:
            p, start, end = get_poly_approx(coords)
        self.offsetted_arch = coords
        h_coords = apply_offset_to_arch(coords, self.offsetted_arch_amount - arch_offset, p)
        l_coords = apply_offset_to_arch(coords, self.offsetted_arch_amount + arch_offset, p)
        self.panorex = self.create_panorex(coords)
        h_panorex = self.create_panorex(h_coords)
        l_panorex = self.create_panorex(l_coords)
        self.LHpanorexes = (l_panorex, h_panorex)

    def compute_side_coords(self):
        """
        Updates side_coords on the new arch
        """
        l_offset, coords, h_offset, derivative = self.coords
        self.side_coords = processing.generate_side_coords(h_offset, l_offset, derivative)

    def compute_side_volume(self):
        """
        Computes and updates the side volume.
        """
        section = self.volume[self.selected_slice]

        # volume of sections of the orthogonal lines
        side_volume = self.line_slice(self.side_coords)

        # rescaling the projection volume properly
        y_ratio = section.shape[0] / side_volume.shape[1]
        width = int(side_volume.shape[2] * y_ratio)
        height = int(side_volume.shape[1] * y_ratio)
        scaled_side_volume = np.ndarray(shape=(side_volume.shape[0], height, width))

        for i in range(side_volume.shape[0]):
            scaled_side_volume[i] = cv2.resize(side_volume[i, :, :], (width, height), interpolation=cv2.INTER_AREA)

        # padding the side volume and rescaling
        scaled_side_volume = cv2.normalize(scaled_side_volume, scaled_side_volume, 0, 1, cv2.NORM_MINMAX)

        # creating RGB volume
        scaled_side_volume = np.tile(scaled_side_volume, (3, 1, 1, 1))  # overlay on the original image (colorful)
        scaled_side_volume = np.moveaxis(scaled_side_volume, 0, -1)

        self.side_volume = scaled_side_volume

    def get_section(self, slice, arch=False, offsets=False, pos=None):
        """
        Returns the slice of the volume with additional drawings:
            - current arch
            - current lower and higher arches
            - position on the arch

        Args:
            arch (bool): display current arch
            offsets (bool): display current lower and higher arches
            pos (int): position on the arch

        Returns:
            np.ndarray: slice of the jaw volume
        """
        section = self.volume[slice]

        if not arch:
            return section

        p, start, end = self.arch_detections[slice]
        arch_rgb = np.tile(section, (3, 1, 1))
        arch_rgb = np.moveaxis(arch_rgb, 0, -1)

        if offsets:  # show arch and coords arches
            l_offset, coords, h_offset, _ = self.coords
            if self.offsetted_arch:
                coords = self.offsetted_arch
            for i in range(len(coords)):
                arch_rgb[int(coords[i][1]), int(coords[i][0])] = (1, 0, 0)
                try:
                    arch_rgb[int(h_offset[i][1]), int(h_offset[i][0])] = (0, 1, 0)
                    arch_rgb[int(l_offset[i][1]), int(l_offset[i][0])] = (0, 1, 0)
                except:
                    continue
            # draw blue line
            if pos is not None:
                if self.side_coords is None:
                    self.compute_side_coords()
                points = self.side_coords[pos]
                for x, y in points:
                    if section.shape[1] > x > 0 and section.shape[0] > y > 0:
                        arch_rgb[int(y), int(x)] = (0, 0, 1)
        else:  # just show the arch
            for sample in range(start, end):
                y_sample = np.clip(p(sample), 0, arch_rgb.shape[0] - 1)
                arch_rgb[int(y_sample), sample, :] = (1, 0, 0)

        return arch_rgb
