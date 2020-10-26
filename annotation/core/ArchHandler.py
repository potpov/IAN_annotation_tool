import os

import cv2
import numpy as np
import json

import processing
import viewer
from Jaw import Jaw
from annotation.actions.Action import SliceChangedAction, TiltedPlanesAnnotationAction
from annotation.actions.History import History
from annotation.components.message.Messenger import Messenger
from annotation.components.message.Strategies import QtMessageStrategy
from annotation.core.AnnotationMasks import AnnotationMasks
from annotation.core.Arch import Arch
from annotation.core.ArchDetections import ArchDetections
from annotation.core.SideVolume import SideVolume, TiltedSideVolume
from annotation.spline.Spline import Spline
from annotation.utils.image import get_coords_by_label_3D, get_mask_by_label, filter_volume_Z_axis, plot
from annotation.utils.math import clip_range, get_poly_approx_
from annotation.utils.metaclasses import SingletonMeta
from conf import labels as l


class ArchHandler(Jaw, metaclass=SingletonMeta):
    LH_OFFSET = 50
    DUMP_FILENAME = 'dump.json'
    ANNOTATED_DICOM_DIRECTORY = 'annotated_dicom'
    EXPORT_GT_VOLUME_FILENAME = 'gt_volume.npy'
    EXPORT_VOLUME_FILENAME = 'volume.npy'

    SIDE_VOLUME_SCALE = 4  # desired scale of side_volume

    def __init__(self, dicomdir_path):
        """
        Class that handles the arch and panorex computing on top of the Jaw class.

        Args:
            dicomdir_path (str): path of the DICOMDIR file

        Attributes:
            dicomdir_path (str): path of the DICOMDIR file
            history (History): History object that memorizes user changes
            selected_slice (int): index of the selected slice of the volume
            arch_detections (ArchDetections): object that stores arches of each slice of the volume
            coords ((list of (float, float), list of (float, float), list of (float, float), list of float)): (l_offset, coords, h_offset, derivative) tuple of the arch for the selected slice of the volume
            spline (Spline): object that models the arch as a Catmull-Rom spline
            arch (Arch): object that stores the coordinates of the arch offsetted while using the application
            LH_pano_arches ((Arch, Arch)): objects that store the coordinates of two arches slightly distant from the arch
            side_coords (list): coordinates of the points that define "side_volume" perimeter
            old_side_coords (list): side_coords of the current SideVolume, used in order not to recompute SideVolume if there are no changes
            side_volume (list): volume of the side views of the jaw volume through the two coords arches
            side_volume_scale (int): multiplier for side_volume images dimensions
            L_canal_spline (Spline): object that models the left canal in the panorex with a Catmull-Rom spline
            R_canal_spline (Spline): object that models the right canal in the panorex with a Catmull-Rom spline
            annotation_masks (AnnotationMasks): object that manages the annotations onto side_volume images
            canal (numpy.ndarray): same as side_volume, but has just the canal (obtained from masks) and it is scaled to original volume dimensions
            gt_delaunay (numpy.ndarray): same as gt_volume, the canal has been smoothed with Delaunay algorithm
            gt_extracted (bool): flags the user has extracted the views from previous annotations
        """
        sup = super()
        self.messenger = Messenger(QtMessageStrategy())
        self.messenger.loading_message(func=lambda: sup.__init__(dicomdir_path), message="Loading DICOM")
        self.dicomdir_path = dicomdir_path
        self.history = History(self, save_func=self.save_state)
        self.selected_slice = None
        self.arch_detections = ArchDetections(self)
        self.coords = None
        self.spline = None
        self.arch = None
        self.LH_pano_arches = None
        self.side_coords = None
        self.old_side_coords = None
        self.side_volume = None
        self.side_volume_scale = self.SIDE_VOLUME_SCALE
        self.L_canal_spline = None
        self.R_canal_spline = None
        self.annotation_masks: AnnotationMasks = None
        self.canal = None
        self.gt_delaunay = np.zeros_like(self.gt_volume)
        self.gt_extracted = False

    ####################
    # ATTRIBUTE UPDATE #
    ####################

    def _initalize_attributes(self, selected_slice=0, data=None):
        """
        Sets class attributes after the selection of the slice.
        It can also initialize attributes from data dump during loading.

        Args:
            selected_slice (int): index of the selected slice in the jaw volume
            data (dict): data to load from
        """
        if data is not None:
            self.selected_slice = data['selected_slice']
            self.spline = Spline(load_from=data['spline'])
            self.L_canal_spline = Spline(load_from=data['L_canal_spline'])
            self.R_canal_spline = Spline(load_from=data['R_canal_spline'])
        else:
            self.selected_slice = selected_slice
            self.history.add(SliceChangedAction(selected_slice))
            p, start, end = self.arch_detections.get(selected_slice)
            l_offset, coords, h_offset, derivative = processing.arch_lines(p, start, end, offset=self.LH_OFFSET)
            self.spline = Spline(coords=coords, num_cp=10)
            self.L_canal_spline = Spline()
            self.R_canal_spline = Spline()

        self.update_coords()
        self.arch = Arch(self, self.coords[1])
        h_arch = self.arch.get_offsetted(-1)
        l_arch = self.arch.get_offsetted(1)
        self.LH_pano_arches = (l_arch, h_arch)

    def compute_initial_state(self, selected_slice=0, data=None, want_side_volume=True):
        """
        Sets class attributes after the selection of the slice.
        Then computes panorexes and side volume.

        Args:
            selected_slice (int): index of the selected slice in the jaw volume
            data (dict): data to load from
            want_side_volume (bool): whether to compute or not side_volume. In most cases, it should.
        """
        self._initalize_attributes(selected_slice, data)
        self.compute_side_coords()
        tilted = self.history.has(TiltedPlanesAnnotationAction)
        want_side_volume and self.compute_side_volume(self.side_volume_scale, tilted=tilted)

    def update_coords(self):
        """Updates the current arch after the changes in the spline."""
        p, start, end = self.spline.get_poly_spline()
        self.arch_detections.set(self.selected_slice, (p, start, end))
        if p is not None:
            self.coords = processing.arch_lines(p, start, end, offset=self.LH_OFFSET)

    def compute_side_coords(self):
        """Updates side_coords on the new arch"""
        l_offset, coords, h_offset, derivative = self.coords
        self.side_coords = processing.generate_side_coords(h_offset, l_offset, derivative)

    def offset_arch(self, arch_offset=0, pano_offset=1):
        """
        Computes/Updates the Arch objects after the offsets.

        Args:
            arch_offset (int): how much to displace the curve from the original coordinates
            pano_offset (int): how much to displace the "parallel" LH offsetted curves
        """
        # reset to initial position
        self.arch.set_arch(self.coords[1])
        if pano_offset != 0:
            h_arch = self.arch.get_offsetted(arch_offset - pano_offset)
            l_arch = self.arch.get_offsetted(arch_offset + pano_offset)
        self.arch.offset(arch_offset)
        if pano_offset == 0:
            h_arch = l_arch = self.arch.copy()
        self.LH_pano_arches = (l_arch, h_arch)

    def tilted(self):
        """
        Whether ArchHandler has SideVolume or TiltedSideVolume as side_volume

        Returns:
            (bool): if True, ArchHandler has tilted side_volume
        """
        if isinstance(self.side_volume, TiltedSideVolume):
            return True
        return False

    def compute_side_volume(self, scale=None, tilted=False):
        """
        Computes and updates side_volume.

        Args:
            scale (float): scale of side volume w.r.t. volume dimensions
            tilted (bool): selects TiltedSideVolume instead of default SideVolume
        """
        # check if needed to recompute side_volume
        if self.old_side_coords is not None \
                and np.array_equal(self.side_coords, self.old_side_coords) \
                and self.tilted() == tilted:
            return
        self.old_side_coords = self.side_coords

        self.side_volume_scale = self.SIDE_VOLUME_SCALE if scale is None else scale

        if tilted:
            self.side_volume = TiltedSideVolume(self, self.side_volume_scale)
        else:
            self.side_volume = SideVolume(self, self.side_volume_scale)

        # configuring annotations_masks
        shape = self.side_volume.get().shape
        if self.annotation_masks is None:
            self.annotation_masks = AnnotationMasks(shape, self)
        else:
            self.annotation_masks.check_shape(shape)

    ###########################
    # VOLUME + ANNOTATION OPS #
    ###########################

    def extract_3D_annotations(self):
        """Transforms 2D annotations on SideVolume into gt_volume"""
        self.annotation_masks.compute_mask_volume()

        self.canal = self.annotation_masks.mask_volume
        if self.canal is None or not self.canal.any():
            return

        self.compute_gt_volume()

    def _compute_gt_volume(self, step_fn=None):
        """
        Transfers the canal computed in AnnotationsMasks.compute_mask_volume() in the original volume position,
        i.e. a curved 3D tube that follows the arch
        """

        def assign_to_gt_volume(self, val, x, y, z):
            x_ = clip_range(x, 0, self.W - 1)
            y_ = clip_range(y, 0, self.H - 1)
            z_ = int(clip_range(z, 0, self.Z - 1))
            gt_volume[z_, floor(y_), floor(x_)] = val
            gt_volume[z_, floor(y_), ceil(x_)] = val
            gt_volume[z_, ceil(y_), floor(x_)] = val
            gt_volume[z_, ceil(y_), ceil(x_)] = val

        from math import floor, ceil
        gt_volume = np.full_like(self.volume, l.UNLABELED, dtype=np.uint8)
        if not self.tilted():
            for z_id, points in enumerate(self.side_coords):
                step_fn is not None and step_fn(z_id, len(self.side_coords))
                for w_id, (x, y) in enumerate(points):
                    if 0 <= int(x) < self.W and 0 <= int(y) < self.H:
                        # # less precise method
                        # gt_volume[:, int(y), int(x)] = self.canal[z_id, :, w_id]

                        # # floor and ceil only CONTOUR and INSIDE labels
                        # z_column = self.canal[z_id, :, w_id]
                        # gt_volume[:, int(y), int(x)] = z_column
                        # for h_id in np.argwhere(np.logical_or(z_column == l.CONTOUR, z_column == l.INSIDE)):
                        #     val = z_column[h_id]
                        #     gt_volume[h_id, floor(y), floor(x)] = val
                        #     gt_volume[h_id, floor(y), ceil(x)] = val
                        #     gt_volume[h_id, ceil(y), floor(x)] = val
                        #     gt_volume[h_id, ceil(y), ceil(x)] = val

                        z_column = self.canal[z_id, :, w_id]

                        # floor and ceil for every label
                        x_ = clip_range(x, 0, self.W - 1)
                        y_ = clip_range(y, 0, self.H - 1)
                        gt_volume[:, floor(y_), floor(x_)] = self.canal[z_id, :, w_id]
                        gt_volume[:, floor(y_), ceil(x_)] = self.canal[z_id, :, w_id]
                        gt_volume[:, ceil(y_), floor(x_)] = self.canal[z_id, :, w_id]
                        gt_volume[:, ceil(y_), ceil(x_)] = self.canal[z_id, :, w_id]
                        for h_id in np.argwhere(z_column == l.INSIDE):
                            assign_to_gt_volume(self, l.INSIDE, x, y, h_id)
                        for h_id in np.argwhere(z_column == l.CONTOUR):
                            assign_to_gt_volume(self, l.CONTOUR, x, y, h_id)

        else:
            for i, (img, plane) in enumerate(zip(self.canal, self.side_volume.planes)):
                step_fn is not None and step_fn(i, len(self.side_coords))
                if plane is None:
                    continue
                if np.array_equal(img, np.full_like(img, l.UNLABELED, dtype=np.uint8)):
                    continue
                X, Y, Z = plane.plane
                for val, x, y, z in np.nditer([img, X, Y, Z]):
                    assign_to_gt_volume(self, val, x, y, z)
                    # gt_volume[z, y, x] = val

        self.set_gt_volume(gt_volume)

    def compute_gt_volume(self):
        """Shows a progress bar while computing gt_volume"""
        self.messenger.progress_message(message="Computing ground truth volume",
                                        func=self._compute_gt_volume,
                                        func_args={})

    def _compute_gt_volume_delaunay(self):
        """Applies Delaunay algorithm in order to have a smoother gt_volume."""
        gt_volume = self.get_gt_volume(labels=[l.CONTOUR, l.INSIDE])
        # gt_volume = get_mask_by_label(self.gt_volume, l.CONTOUR)
        if gt_volume is None or gt_volume.any() == False:
            return
        gt_volume = viewer.delaunay(gt_volume)
        self.gt_delaunay = gt_volume

    def compute_gt_volume_delaunay(self):
        """Extracts annotations, builds gt_volume and computes smoothed gt_volume"""
        self.extract_3D_annotations()
        self.messenger.loading_message(message="Applying Delaunay", func=self._compute_gt_volume_delaunay)
        if self.gt_delaunay is None or self.gt_delaunay.any() == False:
            self.messenger.message(kind="information", title="Delaunay",
                                   message="Cannot apply Delaunay without annotations")

    ###############
    # SAVE | LOAD #
    ###############

    def is_there_data_to_load(self):
        """
        Check if save file exists

        Returns:
            (bool): save file presence
        """
        path = os.path.join(os.path.dirname(self.dicomdir_path), self.DUMP_FILENAME)
        return os.path.isfile(path)

    def save_state(self):
        """Saves ArchHandler state, with History and AnnotationsMasks"""
        data = {}
        data['version'] = 1.0
        data['spline'] = self.spline.get_json()
        data['L_canal_spline'] = self.L_canal_spline.get_json()
        data['R_canal_spline'] = self.R_canal_spline.get_json()
        data['selected_slice'] = self.selected_slice
        with open(os.path.join(os.path.dirname(self.dicomdir_path), self.DUMP_FILENAME), "w") as outfile:
            json.dump(data, outfile)
        self.history.save_()
        if self.annotation_masks is not None:
            self.annotation_masks.save_mask_splines()

    def load_state(self):
        """Loads state for ArchHandler, with History and AnnotationsMasks"""
        path = os.path.join(os.path.dirname(self.dicomdir_path), self.DUMP_FILENAME)
        with open(path, "r") as infile:
            data = json.load(infile)

        self.history.load_()
        self.compute_initial_state(0, data)
        self.annotation_masks.load_mask_splines()

    def _export_annotations_as_dicom(self):
        """Exports the new DICOM with the annotations."""
        self.overwrite_annotations()
        self.save_dicom(os.path.join(os.path.dirname(self.dicomdir_path), self.ANNOTATED_DICOM_DIRECTORY))

    def export_annotations_as_dicom(self):
        """See ArchHandler._export_annotations_as_dicom()"""
        self.extract_3D_annotations()
        self.messenger.loading_message("Saving new DICOM", self._export_annotations_as_dicom)

    def export_annotations_as_imgs(self):
        """Saves annotations as images"""
        self.annotation_masks.export_mask_imgs()

    def export_gt_volume(self):
        """Extracts annotations, builds gt_volume and saves it as npy file"""
        self.extract_3D_annotations()
        self.messenger.loading_message(
            "Saving ground truth volume",
            func=lambda: np.save(os.path.join(os.path.dirname(self.dicomdir_path), self.EXPORT_GT_VOLUME_FILENAME),
                                 self.gt_volume))
        self.messenger.loading_message(
            "Saving volume",
            func=lambda: np.save(os.path.join(os.path.dirname(self.dicomdir_path), self.EXPORT_VOLUME_FILENAME),
                                 self.get_volume(normalized=False))
        )

    def import_gt_volume(self):
        """Imports gt_volume npy file and stores it in gt_volume attribute"""
        if os.path.isfile(os.path.join(os.path.dirname(self.dicomdir_path), self.EXPORT_GT_VOLUME_FILENAME)):
            self.gt_volume = np.load(os.path.dirname(self.dicomdir_path), self.EXPORT_GT_VOLUME_FILENAME)

    ################
    # LOAD FROM GT #
    ################

    def extract_canal_mask_labels_Z(self):
        def correct_labels(img):
            h, w = img.shape
            half = img[:, :w // 2]  # get left half
            left_label = half[half > 0]  # get non zeros
            left_label = np.bincount(left_label).argmax()  # get most frequent label in left half
            if left_label == 1:
                return img
            label_1_to_2 = get_mask_by_label(img, 1)
            label_1_to_2[label_1_to_2 == 1] = 2
            label_2_to_1 = get_mask_by_label(img, 2)
            return label_1_to_2 + label_2_to_1

        gt = np.sum(self.gt_volume, axis=0, dtype=np.uint8)
        gt[gt > 0] = 1
        ret, labels = cv2.connectedComponents(gt)
        if ret != 3:
            raise ValueError("Expected 3 different labels, got {}".format(ret))
        return correct_labels(labels)

    def extract_canal_spline(self, img, label):
        mask = get_mask_by_label(img, label)
        gt_canal = filter_volume_Z_axis(self.gt_volume, mask)
        z, y, x = get_coords_by_label_3D(gt_canal, 1)
        p, start, end = get_poly_approx_(x, z)
        coords = []
        for i, (x_, y_) in enumerate(self.arch.get_arch()):
            if int(start) < x_ < int(end):
                z_ = p(x_)
                coords.append((i, z_))
        return Spline(coords=coords, num_cp=10)

    def extract_data_from_gt(self, load_annotations=True, debug=False):
        if self.gt_volume is None:
            print("gt_volume is None")
            return

        debug and plot(self.create_panorex(self.arch.get_arch(), include_annotations=True), title="panorex+gt")

        gt = np.copy(self.gt_volume)
        gt[gt > 0] = 1

        z, y, x = get_coords_by_label_3D(gt, 1)
        p, start, end = get_poly_approx_(x, y)
        self.arch_detections.set(self.selected_slice, (p, start, end))
        if p is not None:
            self.coords = processing.arch_lines(p, start, end, offset=self.LH_OFFSET)
            self.spline = Spline(coords=self.coords[1], num_cp=10)
            self.update_coords()
            self.arch.update(self.coords[1])
            self.compute_side_coords()

        labels = self.extract_canal_mask_labels_Z()
        debug and plot(labels, "labels")

        self.L_canal_spline = self.extract_canal_spline(labels, 1)
        self.R_canal_spline = self.extract_canal_spline(labels, 2)
        self.gt_extracted = True

        if load_annotations:
            shape = (len(self.side_coords), self.Z, max([len(points) for points in self.side_coords]))
            self.annotation_masks = AnnotationMasks(shape, self)
            self.annotation_masks.load_mask_splines(check_shape=False)

    ###########
    # GETTERS #
    ###########

    def get_panorex(self):
        """
        Returns the panorex.

        Returns:
            (numpy.ndarray): panorex
        """
        return self.arch.get_panorex()

    def get_LH_panorexes(self):
        """
        Returns low and high panorexes.

        Returns:
            ((numpy.ndarray, numpy.ndarray)): panorexes
        """
        l_arch, h_arch = self.LH_pano_arches
        return (l_arch.get_panorex(), h_arch.get_panorex())

    def get_jaw_with_gt(self):
        gt = self.get_gt_volume(labels=[l.CONTOUR, l.INSIDE])
        return self.volume + gt if gt.any() else None

    def get_jaw_with_delaunay(self):
        return self.volume + self.gt_delaunay if self.gt_delaunay.any() else None

    def get_side_volume_slice(self, pos):
        return self.side_volume.get_slice(pos)
