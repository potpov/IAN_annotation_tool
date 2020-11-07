import json
import os
import numpy as np
from datetime import datetime

from annotation.actions.Action import SideVolumeSplineExtractedAction
from annotation.components.message.Messenger import Messenger
from annotation.spline.Spline import ClosedSpline
from annotation.utils.image import export_img, active_contour_balloon
from conf import labels as l


class AnnotationMasks():
    MASK_DIR = 'masks'
    EXPORT_PATH = ""
    EXPORT_MASK_FILENAME = "_mask.png"
    EXPORT_IMG_FILENAME = "_img.png"
    EXPORT_MASK_VOLUME_FILENAME = "masks.npy"
    EXPORT_SIDE_VOLUME_FILENAME = "imgs.npy"
    MASKS_SPLINES_DUMP_FILENAME = "masks_splines_dump.json"
    NUM_CP_LOSS = 10  # higher value means less control points and implies a loss in the spline's precision

    def __init__(self, shape, arch_handler):
        """
        This class stores, handles, saves and load annotation masks.

        Annotations are in a list Spline objects, but this is initialized with None.

        Args:
            shape ((int, int)): shape of side volume
            arch_handler (annotation.core.ArchHandler.ArchHandler): ArchHandler object
        """
        self.n, self.h, self.w = shape
        self.scaling = 1
        self.arch_handler = arch_handler
        self.EXPORT_PATH = os.path.join(os.path.dirname(self.arch_handler.dicomdir_path), self.MASK_DIR)
        self.masks = [None] * self.n
        self.created_from_snake = [False] * self.n
        self.mask_volume = None
        self._edited = False
        self.skip = 0
        self.messenger = Messenger()

    def check_shape(self, new_shape):
        """
        Check if the given shape is the same as the one loaded from file.

        Adapts the object to work with the new shape.

        Args:
            new_shape ((int, int)): shape to check
        """
        n_, h_, w_ = new_shape
        if n_ != self.n:
            # self.messenger.message(kind="Warning", title="Side volume amount of images mismatch",
            #                       message="The loaded annotations expect a different amount of images inside side_volume. Exceeding annotations will be deleted")
            diff = n_ - self.n
            if diff > 0:  # enlarge
                self.masks.extend([None] * diff)
                self.created_from_snake.extend([False] * diff)
            else:  # shrink
                # 'diff' is negative, so I will discard the last 'diff' elements
                self.masks = self.masks[:diff]
                self.created_from_snake = self.created_from_snake[:diff]
        if h_ != self.h or w_ != self.w:
            # self.messenger.message(kind="Warning", title="Side volume shape mismatch",
            #                  message="The shape of the current side volume does not match with the shape of the loaded annotations. This may lead to inconsistency of the annotations.")
            pass
        self.n, self.h, self.w = new_shape

    def compute_mask_image(self, spline, shape, resize_scale=None):
        """
        Computes an image with labels from a spline.

        Args:
            spline (annotation.spline.Spline.Spline): spline source of the mask
            shape ((int, int)): shape of the output image
            resize_scale (float): scaling factor of the image

        Returns:
            (numpy.ndarray): mask image with labels
        """
        if spline is not None:
            return spline.generate_mask(shape, resize_scale)
        else:
            s = shape if resize_scale is None else tuple(map(lambda x: int(x / resize_scale), shape))
            return np.full(s, l.BG, dtype=np.uint8)

    def _compute_mask_volume(self, step_fn=None):
        """
        Stacks mask images (label images) in a volume

        Args:
            step_fn: function to log progress
        """
        scaled_h = int(self.h / self.arch_handler.side_volume_scale)
        scaled_w = int(self.w / self.arch_handler.side_volume_scale)
        shape = (self.n, scaled_h, scaled_w)
        # by default, mask_volume is UNLABELED
        self.mask_volume = np.full(shape, l.UNLABELED, dtype=np.uint8)
        for i, mask in enumerate(self.masks):
            step_fn is not None and step_fn(i, len(self.masks))
            # Get mask_image only if the use could have annotate it.
            # This is because (self.skip + 1) defines which slices to annotate or not.
            # (skip self.skip slices and annotate the next one)
            # If the user cannot annotate a slice, then he gets full(UNLABELED).
            # Otherwise, if he had the possibility to annotate, but there is no annotation, then he gets full(BG).
            if i % (self.skip + 1) == 0 and self.arch_handler.side_volume.get()[i].any():
                mask_img = self.compute_mask_image(mask, (self.h, self.w),
                                                   resize_scale=self.arch_handler.side_volume_scale)
                self.mask_volume[i] = mask_img

    def compute_mask_volume(self):
        """Stacks mask images (label images) in a volume"""
        self.messenger.progress_message(message="Computing 3D canal", func=self._compute_mask_volume, func_args={})

    def set_mask_spline(self, idx, spline, from_snake=False):
        """
        Sets annotation at given index

        Args:
            idx (int): index
            spline (annotation.spline.Spline.Spline): spline (the annotation)
            from_snake (bool): if the annotation was automatically extracted or not
        """
        self._edited = True
        self.created_from_snake[idx] = from_snake
        self.masks[idx] = spline
        return spline

    def get_mask_spline(self, idx, from_snake=False):
        """
        Getter for annotation at given index.
        If there is no annotation, but from_snake argument is True,
        then the annotation is automatically extracted with MorphGAC.

        Args:
            idx (int): index
            from_snake (bool): extract annotation automatically if not exists already
        """
        if self.masks[idx] is None and from_snake is True:
            step = self.skip + 1
            from_idx = idx - step
            init = self.masks[from_idx]
            if init is None:
                from_idx = idx + step
                init = self.masks[from_idx]
            if init is not None:
                #### TEST
                ## Approach with skimage.segmentation.active_contour
                # spline = np.array(init.get_spline())
                # snake = active_contour(self.arch_handler.side_volume[idx], spline, max_iterations=100)
                ####
                img = self.arch_handler.get_side_volume_slice(idx)
                snake = active_contour_balloon(img, init, debug=False)
                if snake is None:
                    return None
                self.arch_handler.history.add(SideVolumeSplineExtractedAction(idx, from_idx))
                self.set_mask_spline(idx, ClosedSpline(coords=snake, num_cp=(len(snake) // self.NUM_CP_LOSS)),
                                     from_snake)
        return self.masks[idx]

    def export_mask_imgs(self):
        """
        Saves:
            - side volume (npy)
            - annotation volume (npy)
            - side volume images (PNG)
            - annotation mask images (PNG)
        """
        self.compute_mask_volume()

        now = datetime.now()
        date_str = "{:04d}{:02d}{:02d}-{:02d}{:02d}{:02d}".format(
            now.year, now.month, now.day, now.hour, now.minute, now.second)

        # prepare mask dir
        masks_dirname = "masks-{}".format(date_str)
        masks_path = os.path.join(self.EXPORT_PATH, masks_dirname)
        if not os.path.exists(masks_path):
            os.makedirs(masks_path)
        np.save(os.path.join(masks_path, self.EXPORT_MASK_VOLUME_FILENAME), self.mask_volume)

        # prepare imgs dir
        sv = self.arch_handler.side_volume
        if sv.original is None:
            print("Could not extract side volume images")
        else:
            imgs_dirname = "imgs-{}".format(date_str)
            imgs_path = os.path.join(self.EXPORT_PATH, imgs_dirname)
            if not os.path.exists(imgs_path):
                os.makedirs(imgs_path)
            np.save(os.path.join(imgs_path, self.EXPORT_SIDE_VOLUME_FILENAME), sv.original)

        for i, img in enumerate(self.mask_volume):
            if not img.any():  # skipping totally black images
                continue
            export_img(img, os.path.join(masks_path, "{}{}".format(i, self.EXPORT_MASK_FILENAME)),
                       maximum=max(l.values()))
            if sv.original is not None:
                export_img(sv.original[i], os.path.join(imgs_path, "{}{}".format(i, self.EXPORT_IMG_FILENAME)))

    def save_mask_splines(self):
        """Saves annotation mask splines on disk, only if there are changes"""
        if not self._edited:
            return
        dump = {
            'n': self.n,
            'h': self.h,
            'w': self.w,
            'scaling': self.arch_handler.side_volume_scale,
            'skip': self.skip,
            'masks': [mask.get_json() if mask is not None else None for mask in self.masks],
            'from_snake': [fs for fs in self.created_from_snake]
        }
        if not os.path.exists(self.EXPORT_PATH):
            os.makedirs(self.EXPORT_PATH)
        with open(os.path.join(self.EXPORT_PATH, self.MASKS_SPLINES_DUMP_FILENAME), "w") as outfile:
            json.dump(dump, outfile)
        self._edited = False

    def load_mask_splines(self, check_shape=True):
        """
        Loads mask splines from disk.

        Args:
            check_shape (bool): whether to check for shape consistency or not
        """
        path = os.path.join(self.EXPORT_PATH, self.MASKS_SPLINES_DUMP_FILENAME)
        if not os.path.isfile(path):
            print("No masks to load")
            return

        with open(path, "r") as infile:
            data = json.load(infile)
        self.n = data['n']
        self.h = data['h']
        self.w = data['w']
        self.scaling = data['scaling']
        self.skip = data['skip'] if 'skip' in data.keys() else 0
        self.masks = [None] * self.n
        self.created_from_snake = [False] * self.n
        for i, spline_dump in enumerate(data['masks']):
            if spline_dump is None:
                spline = None
            else:
                spline = ClosedSpline(load_from=spline_dump)
            from_snake = data['from_snake'][i] if 'from_snake' in data.keys() else False
            self.set_mask_spline(i, spline, from_snake)
        self.handle_scaling_mismatch()
        check_shape and self.check_shape(self.arch_handler.side_volume.get().shape)
        self._edited = False

    def handle_scaling_mismatch(self):
        """
        Rescales the annotation splines if the loaded scale is not the same scaling in ArchHandler.
        """
        if self.scaling != self.arch_handler.side_volume_scale:
            # self.messenger.message("warning", "Scaling mismatch", "The size scale of the volume from which the annotations were taken does not match the current scale. The annotations will be resized and may lose consistency.")
            self.messenger.loading_message(func=self.rescale_annotations, message="Rescaling splines")

    def rescale_annotations(self):
        """Annotation spline rescale"""
        new_masks = []
        rescale_factor = self.arch_handler.side_volume_scale / self.scaling
        for spline in self.masks:
            if spline is not None:
                coords = spline.get_spline(downscale=1 / rescale_factor)
                new_spline = ClosedSpline(coords=coords, num_cp=(len(coords) // int(self.NUM_CP_LOSS * rescale_factor)))
                new_masks.append(new_spline)
            else:
                new_masks.append(None)
        self.masks = new_masks

    ###########
    # SETTERS #
    ###########

    def set_skip(self, skip):
        """Sets the amount of annotations to skip"""
        self.skip = skip
