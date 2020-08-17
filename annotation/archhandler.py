import os

import numpy as np
import cv2
import json

import processing
from Jaw import Jaw
from annotation.actions.Action import SliceChangedAction
from annotation.actions.History import History
from annotation.components.Dialog import LoadingDialog
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
            LHoffsetted_arches (list, list): coordinates of two arches slightly distant from the offsetted_arch
            offsetted_arch_amount (int): value between -LH_OFFSET and LH_OFFSET of the coords of the arch for the panorex
            side_coords (list): coordinates of the points that define "side_volume" perimeter
            side_volume (list): volume of the side views of the jaw volume through the two coords arches
            L_canal_spline (Spline): object that models the left canal in the panorex with a Catmull-Rom spline
            R_canal_spline (Spline): object that models the right canal in the panorex with a Catmull-Rom spline
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
        self.LHoffsetted_arches = None
        self.offsetted_arch_amount = 0
        self.side_coords = None
        self.side_volume = None
        self.side_volume_scale = None
        self.L_canal_spline = None
        self.R_canal_spline = None
        self.compute_arch_dialog()

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

    def compute_arch_dialog(self):
        dialog = LoadingDialog(self.compute_arch, message="Computing arches")
        dialog.exec_()

    def save_state(self):
        data = {}
        data['version'] = 1.0
        data['spline'] = self.spline.get_json()
        data['L_canal_spline'] = self.L_canal_spline.get_json()
        data['R_canal_spline'] = self.R_canal_spline.get_json()
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

        old_spline_cp = self.spline.cp

        with open(path, "r") as infile:
            data = json.load(infile)
            self.initalize_attributes(data['selected_slice'])
            self.spline.read_json(data['spline'], build_spline=True)
            self.L_canal_spline.read_json(data['L_canal_spline'], build_spline=True)
            self.R_canal_spline.read_json(data['R_canal_spline'], build_spline=True)
            self.history.load(data['history'])

            if old_spline_cp != self.spline.cp:
                self.offsetted_arch = self.spline.get_spline()
                self.update_coords()
                self.compute_panorexes()
                self.compute_side_coords()
                self.compute_side_volume_dialog()

        print("loaded")

    def initalize_attributes(self, selected_slice):
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
        self.L_canal_spline = Spline([], 0)
        self.R_canal_spline = Spline([], 0)
        self.update_coords()
        self.offsetted_arch = self.spline.get_spline()
        h_coords = apply_offset_to_arch(self.offsetted_arch, -1, p)
        l_coords = apply_offset_to_arch(self.offsetted_arch, +1, p)
        self.LHoffsetted_arches = (l_coords, h_coords)

    def compute_initial_state(self, selected_slice):
        """
        Sets class attributes after the selection of the slice.
        Then computes panorexes and side volume.

        Args:
            selected_slice (int): index of the selected slice in the jaw volume
        """
        self.initalize_attributes(selected_slice)
        self.compute_panorexes()
        self.compute_side_coords()
        self.compute_side_volume_dialog()

    def compute_initial_state_dialog(self, selected_slice):
        dialog = LoadingDialog(func=lambda: self.compute_initial_state(selected_slice),
                               message="Computing initial state")
        dialog.exec_()

    def update_coords(self):
        """
        Updates the current arch after the changes in the spline.
        Also updates the offsetted arches.
        """
        p, start, end = self.spline.get_poly_spline()
        self.arch_detections[self.selected_slice] = (p, start, end)
        self.coords = processing.arch_lines(p, start, end, offset=self.LH_OFFSET)

    def compute_offsetted_arch(self, offset_amount=0, arch_offset=1, p=None):
        """
        Computes the offsetted coordinates of an arch, starting from its polynomial approximation.

        Args:
            offset_amount (int): how much to displace the curve
            arch_offset (int): how much to displace the "parallel" LH offsetted curves
            p (np.poly1d): polynomial approximation of the arch

        Returns:
            list of (float, float): list of xy coordinates of the new offsetted arch
        """
        _, coords, _, _ = self.coords

        if p is None:
            p, _, _ = self.arch_detections[self.selected_slice]

        new_offset = apply_offset_to_arch(coords, offset_amount, p)
        h_coords = apply_offset_to_arch(coords, offset_amount - arch_offset, p)
        l_coords = apply_offset_to_arch(coords, offset_amount + arch_offset, p)
        self.offsetted_arch_amount = offset_amount
        self.offsetted_arch = new_offset
        self.LHoffsetted_arches = (l_coords, h_coords)

    def compute_panorexes(self):
        """
        Computes and updates panorex and LHpanorexes, given a new set of coordinates.
        If not specified, it uses the class ones.

        Args:
            arch_offset (int): coords of the lateral panorexes from the main one
        """

        self.panorex = self.create_panorex(self.offsetted_arch)
        h_panorex = self.create_panorex(self.LHoffsetted_arches[1])
        l_panorex = self.create_panorex(self.LHoffsetted_arches[0])
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
        self.side_volume_scale = y_ratio
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

    def compute_side_volume_dialog(self):
        dialog = LoadingDialog(func=self.compute_side_volume, message="Computing side volume")
        dialog.exec_()

    def get_section(self, slice, arch=False, offsets=False, pos=None):
        """
        Returns the slice of the volume with additional drawings:
            - current arch
            - current lower and higher arches
            - position on the arch

        Args:
            slice (int): index where to slice the volume
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
