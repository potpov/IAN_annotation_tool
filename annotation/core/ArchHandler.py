import os

import numpy as np
import json

import processing
import viewer
from Jaw import Jaw
from annotation.actions.Action import SliceChangedAction
from annotation.actions.History import History
from annotation.core.AnnotationMasks import AnnotationMasks
from annotation.components.Dialog import LoadingDialog, ProgressLoadingDialog
from annotation.core.Arch import Arch
from annotation.core.ArchDetections import ArchDetections
from annotation.core.SideVolume import SideVolume, TiltedSideVolume
from annotation.spline.Spline import Spline
from annotation.utils.math import clip_range
from conf import labels as l


class ArchHandler(Jaw):
    LH_OFFSET = 50
    DUMP_FILENAME = 'dump.json'
    ANNOTATED_DICOM_DIRECTORY = 'annotated_dicom'
    EXPORT_GT_VOLUME_FILENAME = 'gt_volume.npy'

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
        """
        sup = super()
        LoadingDialog(func=lambda: sup.__init__(dicomdir_path), message="Loading DICOM")
        self.dicomdir_path = dicomdir_path
        self.history = History(save_func=self.save_state)
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
        self.annotation_masks = None
        self.canal = None
        self.gt_delaunay = np.zeros_like(self.gt_volume)

    ####################
    # ATTRIBUTE UPDATE #
    ####################

    def _initalize_attributes(self, selected_slice=0, data=None):
        """
        Sets class attributes after the selection of the slice.
        It can also initialize attributes from data dump during loading.

        Args:
            selected_slice (int): index of the selected slice in the jaw volume
        """
        if data is not None:
            self.selected_slice = data['selected_slice']
            self.history.load(data['history'])
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

    def compute_initial_state(self, selected_slice=0, data=None):
        """
        Sets class attributes after the selection of the slice.
        Then computes panorexes and side volume.

        Args:
            selected_slice (int): index of the selected slice in the jaw volume
        """
        self._initalize_attributes(selected_slice, data)
        self.compute_side_coords()
        self.compute_side_volume(self.side_volume_scale)

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
        gt_volume = np.full_like(self.volume, l.UNLABELED, dtype=np.uint8)
        if not self.tilted():
            for z_id, points in enumerate(self.side_coords):
                step_fn is not None and step_fn(z_id, len(self.side_coords))
                for w_id, (x, y) in enumerate(points):
                    if 0 <= int(x) < self.W and 0 <= int(y) < self.H:
                        gt_volume[:, int(y), int(x)] = self.canal[z_id, :, w_id]
        else:
            for i, (img, plane) in enumerate(zip(self.canal, self.side_volume.planes)):
                step_fn is not None and step_fn(i, len(self.side_coords))
                if plane is None:
                    continue
                X, Y, Z = plane.plane
                bool_mask = img.astype(np.bool_)
                if not bool_mask.any():
                    continue
                img = img[bool_mask]
                X = X[bool_mask]
                Y = Y[bool_mask]
                Z = Z[bool_mask]
                for val, x, y, z in np.nditer([img, X, Y, Z]):
                    x = int(clip_range(x, 0, self.W - 1))
                    y = int(clip_range(y, 0, self.H - 1))
                    z = int(clip_range(z, 0, self.Z - 1))
                    gt_volume[z, y, x] = val
        self.set_gt_volume(gt_volume)

    def compute_gt_volume(self):
        """Calls a ProgressLoadingDialod to compute gt_volume"""
        pld = ProgressLoadingDialog("Computing ground truth volume")
        pld.set_function(lambda: self._compute_gt_volume(step_fn=pld.get_signal()))
        pld.start()

    def _compute_gt_volume_delaunay(self):
        """Applies Delaunay algorithm in order to have a smoother gt_volume."""
        if self.gt_volume is None or self.gt_volume.any() == False:
            return
        gt_volume = self.get_simple_gt_volume()
        gt_volume = viewer.delaunay(gt_volume)
        self.gt_delaunay = gt_volume

    def compute_gt_volume_delaunay(self):
        """Extracts annotations, builds gt_volume and computes smoothed gt_volume"""
        self.extract_3D_annotations()
        LoadingDialog(self._compute_gt_volume_delaunay, "Applying Delaunay")

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
        data['history'] = self.history.dump()
        with open(os.path.join(os.path.dirname(self.dicomdir_path), self.DUMP_FILENAME), "w") as outfile:
            json.dump(data, outfile)
        if self.annotation_masks is not None:
            self.annotation_masks.export_mask_splines()
        print("Saved")

    def load_state(self):
        """Loads state for ArchHandler, with History and AnnotationsMasks"""
        path = os.path.join(os.path.dirname(self.dicomdir_path), self.DUMP_FILENAME)
        with open(path, "r") as infile:
            data = json.load(infile)

        self.compute_initial_state(0, data)
        self.annotation_masks.load_mask_splines()
        print("Loaded")

    def _export_annotations_as_dicom(self):
        """Exports the new DICOM with the annotations."""
        self.overwrite_annotations()
        self.save_dicom(os.path.join(os.path.dirname(self.dicomdir_path), self.ANNOTATED_DICOM_DIRECTORY))

    def export_annotations_as_dicom(self):
        """See ArchHandler._export_annotations_as_dicom()"""
        self.extract_3D_annotations()
        LoadingDialog(self._export_annotations_as_dicom, "Saving new DICOM")

    def export_annotations_as_imgs(self):
        """Saves annotations as images"""
        self.annotation_masks.export_mask_imgs()

    def export_gt_volume(self):
        """Extracts annotations, builds gt_volume and saves it as npy file"""
        self.extract_3D_annotations()
        LoadingDialog(lambda: np.save(os.path.join(os.path.dirname(self.dicomdir_path), self.EXPORT_GT_VOLUME_FILENAME),
                                      self.gt_volume), "Saving ground truth volume")

    def import_gt_volume(self):
        """Imports gt_volume npy file and stores it in gt_volume attribute"""
        if os.path.isfile(os.path.join(os.path.dirname(self.dicomdir_path), self.EXPORT_GT_VOLUME_FILENAME)):
            self.gt_volume = np.load(os.path.dirname(self.dicomdir_path), self.EXPORT_GT_VOLUME_FILENAME)

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
        gt = self.get_simple_gt_volume()
        return self.volume + gt if gt.any() else None

    def get_jaw_with_delaunay(self):
        return self.volume + self.gt_delaunay if self.gt_delaunay.any() else None

    def get_side_volume_slice(self, pos):
        return self.side_volume.get_slice(pos)