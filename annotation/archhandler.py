import os

import numpy as np
import cv2
import json

import processing
import viewer
from Jaw import Jaw
from Plane import Plane
from annotation.actions.Action import SliceChangedAction
from annotation.actions.History import History
from annotation.annotation_masks import AnnotationMasks
from annotation.components.Dialog import LoadingDialog
from annotation.spline.spline import Spline
from annotation.utils import apply_offset_to_arch


class ArchHandler(Jaw):
    LH_OFFSET = 50
    DUMP_FILENAME = 'dump.json'
    ANNOTATED_DICOM_DIRECTORY = 'annotated_dicom'
    SIDE_VOLUME_SCALE = 3  # desired scale of side_volume

    def __init__(self, dicomdir_path):
        """
        Class that handles the arch and panorex computing on top of the Jaw class.

        Args:
            dicomdir_path (str): path of the DICOMDIR file

        Attributes:
            dicomdir_path (str): path of the DICOMDIR file
            history (History): History object that memorizes user changes
            selected_slice (int): index of the selected slice of the volume
            arch_detections (list of (numpy.poly1d, float, float): list of tuples of each arch of each slice of the volume
            coords ((list of (float, float), list of (float, float), list of (float, float), list of float)): (l_offset, coords, h_offset, derivative) tuple of the arch for the selected slice of the volume
            spline (Spline): object that models the arch as a Catmull-Rom spline
            panorex (numpy.ndarray): panorex computed on one set of coordinates
            LHpanorexes ((numpy.ndarray, numpy.ndarray)): (l_panorex, h_panorex) tuple of panorexes offsetted from the main one
            offsetted_arch (list of (float, float)): coordinates of the main arch offsetted by "offsetted_arch_amount"
            LHoffsetted_arches ((list of (float, float), list of (float, float))): coordinates of two arches slightly distant from the offsetted_arch
            offsetted_arch_amount (int): value between -LH_OFFSET and LH_OFFSET of the coords of the arch for the panorex
            side_coords (list): coordinates of the points that define "side_volume" perimeter
            side_volume (list): volume of the side views of the jaw volume through the two coords arches
            side_volume_scale (int): multiplier for side_volume images dimensions
            L_canal_spline (Spline): object that models the left canal in the panorex with a Catmull-Rom spline
            R_canal_spline (Spline): object that models the right canal in the panorex with a Catmull-Rom spline
            annotation_masks (AnnotationMasks): object that manages the annotations onto side_volume images
            canal (numpy.ndarray): same as side_volume, but has just the canal (obtained from masks) and it is scaled to original volume dimensions
            gt_delaunay (numpy.ndarray): same as gt_volume, the canal has been smoothed with delaunay algorithm
        """
        sup = super()
        LoadingDialog(func=lambda: sup.__init__(dicomdir_path), message="Loading DICOM").exec_()
        self.dicomdir_path = dicomdir_path
        self.history = History()
        self.selected_slice = None
        self.arch_detections = [None] * self.Z
        self.coords = None
        self.spline = None
        self.panorex = None
        self.LHpanorexes = None
        self.offsetted_arch = None
        self.LHoffsetted_arches = None
        self.offsetted_arch_amount = 0
        self.side_coords = None
        self.side_volume = None
        self.side_volume_scale = 1
        self.L_canal_spline = None
        self.R_canal_spline = None
        self.annotation_masks = None
        self.canal = None
        self.gt_delaunay = np.zeros_like(self.gt_volume)
        self.t_side_volume = None

    def is_there_data_to_load(self):
        path = os.path.join(os.path.dirname(self.dicomdir_path), self.DUMP_FILENAME)
        return os.path.isfile(path)

    def compute_all_arch_detections(self):
        """
        DEPRECATED

        Computes the arch for each slice of the jaw volume.
        """
        self.arch_detections = []
        for i, section in enumerate(self.volume):
            self.compute_single_arch_detection(i)

    def compute_single_arch_detection(self, i):
        try:
            self.arch_detections[i] = processing.arch_detection(self.volume[i])
        except:
            self.arch_detections[i] = None

    def get_arch_detection(self, i):
        if self.arch_detections[i] is None:
            self.compute_single_arch_detection(i)
        return self.arch_detections[i]

    def set_arch_detection(self, i, p_start_end):
        self.arch_detections[i] = p_start_end

    def compute_arch_dialog(self):
        """DEPRECATED"""
        LoadingDialog(self.compute_all_arch_detections, message="Computing arches").exec_()

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
        if self.annotation_masks is not None:
            self.annotation_masks.export_mask_splines()
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
                self.compute_offsetted_arch(pano_offset=0)
                self.compute_panorexes()
                self.compute_side_coords()
                self.compute_side_volume_dialog(self.SIDE_VOLUME_SCALE)

        self.annotation_masks.load_mask_splines()
        print("loaded")

    def initalize_attributes(self, selected_slice):
        """
        Sets class attributes after the selection of the slice.

        Args:
            selected_slice (int): index of the selected slice in the jaw volume
        """
        self.selected_slice = selected_slice
        self.history.add(SliceChangedAction(selected_slice))
        p, start, end = self.get_arch_detection(selected_slice)
        l_offset, coords, h_offset, derivative = processing.arch_lines(p, start, end, offset=self.LH_OFFSET)
        self.coords = (l_offset, coords, h_offset, derivative)
        self.spline = Spline(coords, 10)
        self.L_canal_spline = Spline([], 0)
        self.R_canal_spline = Spline([], 0)
        self.update_coords()
        self.offsetted_arch = self.coords[1]
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
        self.compute_side_volume_dialog(self.SIDE_VOLUME_SCALE)

    def compute_initial_state_dialog(self, selected_slice):
        LoadingDialog(func=lambda: self.compute_initial_state(selected_slice),
                      message="Computing initial state").exec_()

    def update_coords(self):
        """
        Updates the current arch after the changes in the spline.
        Also updates the offsetted arches.
        """
        p, start, end = self.spline.get_poly_spline()
        self.set_arch_detection(self.selected_slice, (p, start, end))
        self.coords = processing.arch_lines(p, start, end, offset=self.LH_OFFSET)

    def compute_offsetted_arch(self, offset_amount=0, pano_offset=1, p=None):
        """
        Computes the offsetted coordinates of an arch, starting from its polynomial approximation.

        Args:
            offset_amount (int): how much to displace the curve
            pano_offset (int): how much to displace the "parallel" LH offsetted curves
            p (numpy.poly1d): polynomial approximation of the arch

        Returns:
            list of (float, float): list of xy coordinates of the new offsetted arch
        """
        _, coords, _, _ = self.coords

        if p is None:
            p, _, _ = self.get_arch_detection(self.selected_slice)

        new_offset = apply_offset_to_arch(coords, offset_amount, p)
        if pano_offset == 0:
            h_coords = l_coords = new_offset
        else:
            h_coords = apply_offset_to_arch(coords, offset_amount - pano_offset, p)
            l_coords = apply_offset_to_arch(coords, offset_amount + pano_offset, p)
        self.offsetted_arch_amount = offset_amount
        self.offsetted_arch = new_offset
        self.LHoffsetted_arches = (l_coords, h_coords)

    def compute_panorexes(self):
        """
        Computes and updates panorex and LHpanorexes, given a new set of coordinates.
        If not specified, it uses the class ones.

        Args:
            pano_offset (int): coords of the lateral panorexes from the main one
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

    def compute_side_volume(self, scale=None):
        """
        Computes and updates the side volume.
        """
        section = self.volume[self.selected_slice]

        # volume of sections of the orthogonal lines
        side_volume = self.line_slice(self.side_coords)

        # rescaling the projection volume properly
        y_ratio = section.shape[0] / side_volume.shape[1] if scale is None else scale
        self.side_volume_scale = y_ratio
        width = int(side_volume.shape[2] * y_ratio)
        height = int(side_volume.shape[1] * y_ratio)
        scaled_side_volume = np.ndarray(shape=(side_volume.shape[0], height, width))

        for i in range(side_volume.shape[0]):
            scaled_side_volume[i] = cv2.resize(side_volume[i, :, :], (width, height), interpolation=cv2.INTER_AREA)

        # padding the side volume and rescaling
        scaled_side_volume = cv2.normalize(scaled_side_volume, scaled_side_volume, 0, 1, cv2.NORM_MINMAX)

        self.side_volume = scaled_side_volume

        # configuring annotations_masks
        if self.annotation_masks is None:
            self.annotation_masks = AnnotationMasks(self.side_volume.shape, self)
        else:
            self.annotation_masks.check_shape(self.side_volume.shape)

    def compute_side_volume_dialog(self, scale=None):
        LoadingDialog(func=lambda: self.compute_side_volume(scale=scale), message="Computing side volume").exec_()

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
            numpy.ndarray: slice of the jaw volume
        """
        section = self.volume[slice]

        if not arch:
            return section

        p, start, end = self.get_arch_detection(slice)
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
            for sample in range(int(start), int(end)):
                y_sample = np.clip(p(sample), 0, arch_rgb.shape[0] - 1)
                arch_rgb[int(y_sample), sample, :] = (1, 0, 0)

        return arch_rgb

    def extract_annotations(self):
        """
        Method that wraps some steps in order to extract an annotated volume, starting from AnnotationMasks splines.
        """
        LoadingDialog(self.annotation_masks.compute_mask_volume, "Computing 3D canal").exec_()
        self.canal = self.annotation_masks.mask_volume
        if self.canal is None or not self.canal.any():
            return
        LoadingDialog(self.compute_gt_volume, "Computing ground truth volume").exec_()
        LoadingDialog(self.save_annotations_dicom, "Saving new DICOMs").exec_()
        LoadingDialog(self.compute_gt_volume_delaunay, "Applying delaunay").exec_()

    def compute_gt_volume(self):
        """
        Transfers the canal computed in compute_3d_canal in the original volume position, following the arch.
        """
        gt_volume = np.zeros_like(self.volume)
        for z_id, points in enumerate(self.side_coords):
            for w_id, (x, y) in enumerate(points):
                if 0 <= int(x) < self.W and 0 <= int(y) < self.H:
                    gt_volume[:, int(y), int(x)] = self.canal[z_id, :, w_id]
        self.set_gt_volume(gt_volume)

    def save_annotations_dicom(self):
        """
        Exports the new DICOM with the annotations.
        """
        self.overwrite_annotations()
        self.save_dicom(os.path.join(os.path.dirname(self.dicomdir_path), self.ANNOTATED_DICOM_DIRECTORY))

    def compute_gt_volume_delaunay(self):
        """
        Applies delaunay algorithm in order to have a smoother gt_volume
        """
        gt_volume = viewer.delaunay(self.gt_volume)
        self.gt_delaunay = gt_volume

    def get_jaw_with_gt(self):
        return self.volume + self.gt_volume if self.gt_volume.any() else None

    def get_jaw_with_delaunay(self):
        return self.volume + self.gt_delaunay if self.gt_delaunay.any() else None

    def compute_tilted_side_volume(self, spline: Spline):
        if spline is None:
            return
        n, h, w = self.side_volume.shape
        tilted = np.zeros((n, int(h / self.side_volume_scale), int(w / self.side_volume_scale)))
        p, start, end = spline.get_poly_spline()
        derivative = np.polyder(p, 1)
        # m = -1 / derivative

        for x in range(0, n, 10):
            if x in range(int(start), int(end)):
                side_coord = self.side_coords[x]
                plane = Plane(self.Z, len(side_coord))
                plane.from_line(side_coord)
                angle = -np.degrees(np.arctan(derivative(x)))
                plane.tilt_z(angle, p(x))
                cut = self.plane_slice(plane)
                print("cutting x:{}".format(x))
                tilted[x] = cut

        width = int(tilted.shape[2] * self.side_volume_scale)
        height = int(tilted.shape[1] * self.side_volume_scale)
        scaled_tilted = np.ndarray(shape=(tilted.shape[0], height, width))

        for i in range(tilted.shape[0]):
            scaled_tilted[i] = cv2.resize(tilted[i, :, :], (width, height), interpolation=cv2.INTER_AREA)

        # padding the side volume and rescaling
        scaled_tilted = cv2.normalize(scaled_tilted, scaled_tilted, 0, 1, cv2.NORM_MINMAX)
        self.t_side_volume = scaled_tilted
