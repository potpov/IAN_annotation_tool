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
            tilted (bool): whether to use t_side_volume or not
            t_side_volume (numpy.ndarray): same as side_volume, but contains the tilted planes
            autosave (bool): whether to save on Actions or not
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
        self.tilted = False
        self.t_side_volume = None
        self.autosave = False

    def set_autosave(self, autosave):
        self.autosave = autosave
        self.history.set_autosave(autosave)

    def is_there_data_to_load(self):
        path = os.path.join(os.path.dirname(self.dicomdir_path), self.DUMP_FILENAME)
        return os.path.isfile(path)

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
        print("Saved")

    def load_state(self):
        path = os.path.join(os.path.dirname(self.dicomdir_path), self.DUMP_FILENAME)
        with open(path, "r") as infile:
            data = json.load(infile)

        self.compute_initial_state(0, data)
        self.annotation_masks.load_mask_splines()
        print("Loaded")

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
        """
        Updates the current arch after the changes in the spline.
        Also updates the offsetted arches.
        """
        p, start, end = self.spline.get_poly_spline()
        self.arch_detections.set(self.selected_slice, (p, start, end))
        if p is not None:
            self.coords = processing.arch_lines(p, start, end, offset=self.LH_OFFSET)

    def compute_side_coords(self):
        """
        Updates side_coords on the new arch
        """
        l_offset, coords, h_offset, derivative = self.coords
        self.side_coords = processing.generate_side_coords(h_offset, l_offset, derivative)

    def offset_arch(self, arch_offset=0, pano_offset=1):
        """
        Computes the offsetted coordinates of an arch.

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

    def compute_side_volume(self, scale=None, tilted=False):
        """
        Computes and updates the side volume.

        Args:
            scale (float): scale of side volume w.r.t. volume dimensions
        """

        self.side_volume_scale = self.SIDE_VOLUME_SCALE if scale is None else scale
        if tilted:
            self.tilted = tilted
            self.t_side_volume = TiltedSideVolume(self, self.side_volume_scale)

        # check if needed to recompute side_volume
        if self.old_side_coords is not None and np.array_equal(self.side_coords, self.old_side_coords):
            return
        self.old_side_coords = self.side_coords
        self.side_volume = SideVolume(self, self.side_volume_scale)

        # configuring annotations_masks
        shape = self.side_volume.get().shape
        if self.annotation_masks is None:
            self.annotation_masks = AnnotationMasks(shape, self)
        else:
            self.annotation_masks.check_shape(shape)

    def extract_3D_annotations(self):
        """
        Method that wraps some steps in order to extract an annotated volume, starting from AnnotationMasks splines.
        """
        if not self.tilted:
            pld = ProgressLoadingDialog("Computing 3D canal")
            pld.set_function(lambda: self.annotation_masks.compute_mask_volume(step_fn=pld.get_signal()))
            pld.start()
            self.canal = self.annotation_masks.mask_volume
            if self.canal is None or not self.canal.any():
                return
            LoadingDialog(self.compute_gt_volume, "Computing ground truth volume")
        else:
            pld = ProgressLoadingDialog("Computing ground truth volume")
            pld.set_function(lambda: self.annotation_masks.compute_mask_volume_tilted(step_fn=pld.get_signal()))
            pld.start()
        LoadingDialog(self.export_annotations_as_dicom, "Saving new DICOMs")
        LoadingDialog(self.compute_gt_volume_delaunay, "Applying Delaunay")

    def compute_gt_volume(self):
        """Transfers the canal computed in compute_3d_canal in the original volume position, following the arch."""
        gt_volume = np.zeros_like(self.volume)
        for z_id, points in enumerate(self.side_coords):
            for w_id, (x, y) in enumerate(points):
                if 0 <= int(x) < self.W and 0 <= int(y) < self.H:
                    gt_volume[:, int(y), int(x)] = self.canal[z_id, :, w_id]
        self.set_gt_volume(gt_volume)

    def export_annotations_as_dicom(self):
        """Exports the new DICOM with the annotations."""
        self.overwrite_annotations()
        self.save_dicom(os.path.join(os.path.dirname(self.dicomdir_path), self.ANNOTATED_DICOM_DIRECTORY))

    def compute_gt_volume_delaunay(self):
        """Applies delaunay algorithm in order to have a smoother gt_volume."""
        gt_volume = viewer.delaunay(self.gt_volume)
        self.gt_delaunay = gt_volume

    def get_jaw_with_gt(self):
        return self.volume + self.gt_volume if self.gt_volume.any() else None

    def get_jaw_with_delaunay(self):
        return self.volume + self.gt_delaunay if self.gt_delaunay.any() else None

    def get_side_volume_slice(self, pos, tilted=False):
        if tilted and self.t_side_volume is not None:
            return self.t_side_volume.get_slice(pos)
        return self.side_volume.get_slice(pos)
