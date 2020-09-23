import json
import os
import numpy as np
from datetime import datetime

from annotation.actions.Action import SideVolumeSplineExtractedAction
from annotation.components.Dialog import show_message_box, LoadingDialog
from annotation.spline.Spline import ClosedSpline
from annotation.utils.image import export_img, active_contour_balloon
from annotation.utils.math import clip_range


class AnnotationMasks():
    MASK_DIR = 'masks'
    EXPORT_IMGS_PATH = ""
    EXPORT_IMGS_FILENAME = "_mask.jpg"
    DUMP_MASKS_SPLINES_FILENAME = "masks_splines_dump.json"
    NUM_CP_LOSS = 10  # higher values mean less control points and implies a loss in the spline's precision

    def __init__(self, shape, arch_handler):
        self.n, self.h, self.w = shape
        self.scaling = 1
        self.arch_handler = arch_handler
        self.EXPORT_IMGS_PATH = os.path.join(os.path.dirname(self.arch_handler.dicomdir_path), self.MASK_DIR)
        self.masks = [None] * self.n
        self.created_from_snake = [False] * self.n
        self.mask_volume = None
        self.edited = True

    def check_shape(self, new_shape):
        n_, h_, w_ = new_shape
        if n_ != self.n:
            show_message_box(kind="Warning", title="Side volume amount of images mismatch",
                             message="The loaded annotations expect a different amount of images inside side_volume. Exceeding annotations will be deleted")
            diff = n_ - self.n
            if diff > 0:  # enlarge
                self.masks.extend([None] * diff)
                self.created_from_snake.extend([False] * diff)
            else:  # shrink
                # 'diff' is negative, so I will discard the last 'diff' elements
                self.masks = self.masks[:diff]
                self.created_from_snake = self.created_from_snake[:diff]
        if h_ != self.h or w_ != self.w:
            show_message_box(kind="Warning", title="Side volume shape mismatch",
                             message="The shape of the current side volume does not match with the shape of the loaded annotations. This may lead to inconsistency of the annotations.")
        self.n, self.h, self.w = new_shape

    def compute_mask_image(self, spline, shape, resize_shape=None):
        if spline is not None:
            return spline.generate_mask(shape, resize_shape)
        else:
            return np.zeros(resize_shape or shape, dtype=np.uint8)

    def compute_mask_volume(self, step_fn=None):
        scaled_h = int(self.h / self.arch_handler.side_volume_scale)
        scaled_w = int(self.w / self.arch_handler.side_volume_scale)
        shape = (self.n, scaled_h, scaled_w)
        self.mask_volume = np.zeros(shape, dtype=np.uint8)
        for i, mask in enumerate(self.masks):
            step_fn is not None and step_fn(i, len(self.masks))
            mask_img = self.compute_mask_image(mask, (self.h, self.w), resize_shape=shape[1:])
            mask_img[mask_img < 40] = 0
            mask_img[mask_img > 0] = 1
            mask_img = mask_img.astype(np.bool_)
            self.mask_volume[i, mask_img] = 1

    def compute_mask_volume_tilted(self, step_fn=None):
        scaled_h = int(self.h / self.arch_handler.side_volume_scale)
        scaled_w = int(self.w / self.arch_handler.side_volume_scale)
        shape = (self.n, scaled_h, scaled_w)
        self.mask_volume = np.zeros(shape, dtype=np.uint8)
        self.arch_handler.gt_volume = np.zeros_like(self.arch_handler.volume)
        for i, (mask, plane) in enumerate(zip(self.masks, self.arch_handler.t_side_volume.planes)):
            step_fn is not None and step_fn(i, len(self.masks))
            mask_img = self.compute_mask_image(mask, (self.h, self.w), resize_shape=shape[1:])
            mask_img[mask_img < 40] = 0
            mask_img[mask_img > 0] = 1
            if plane is None:
                continue
            X, Y, Z = plane.plane
            for m, x, y, z in np.nditer([mask_img, X, Y, Z]):
                x = int(clip_range(x, 0, self.arch_handler.W - 1))
                y = int(clip_range(y, 0, self.arch_handler.H - 1))
                z = int(clip_range(z, 0, self.arch_handler.Z - 1))
                self.arch_handler.gt_volume[z, y, x] = m

    def set_mask_spline(self, idx, spline, from_snake=False):
        self.edited = True
        self.created_from_snake[idx] = from_snake
        self.masks[idx] = spline
        return spline

    def get_mask_spline(self, idx, from_snake=False, tilted=False):
        if self.masks[idx] is None and from_snake is True:
            from_idx = idx - 1
            init = self.masks[from_idx]
            if init is None:
                from_idx = idx + 1
                init = self.masks[from_idx]
            if init is not None:
                ####
                ## Approach with skimage.segmentation.active_contour
                # spline = np.array(init.get_spline())
                # snake = active_contour(self.arch_handler.side_volume[idx], spline, max_iterations=100)
                ####
                img = self.arch_handler.side_volume.get_slice(idx) if not tilted \
                    else self.arch_handler.t_side_volume.get_slice(idx)
                snake = active_contour_balloon(img, init, debug=False)
                if snake is None:
                    return None
                self.arch_handler.history.add(SideVolumeSplineExtractedAction(idx, from_idx))
                self.set_mask_spline(idx, ClosedSpline(coords=snake, num_cp=(len(snake) // self.NUM_CP_LOSS)),
                                     from_snake)

        return self.masks[idx]

    def export_mask_imgs(self):
        if self.mask_volume is None or self.edited:
            self.compute_mask_volume()
        now = datetime.now()
        directory_name = "masks-{:04d}{:02d}{:02d}-{:02d}{:02d}{:02d}".format(
            now.year, now.month, now.day, now.hour, now.minute, now.second)
        path = os.path.join(self.EXPORT_IMGS_PATH, directory_name)
        if not os.path.exists(path):
            os.makedirs(path)
        for i, img in enumerate(self.mask_volume):
            if not img.any():  # skipping totally black images
                continue
            filename = "{}{}".format(i, self.EXPORT_IMGS_FILENAME)
            export_img(img, os.path.join(path, filename))
        self.edited = False

    def export_mask_splines(self):
        dump = {
            'n': self.n,
            'h': self.h,
            'w': self.w,
            'scaling': self.arch_handler.side_volume_scale,
            'masks': [mask.get_json() if mask is not None else None for mask in self.masks]
        }
        if not os.path.exists(self.EXPORT_IMGS_PATH):
            os.makedirs(self.EXPORT_IMGS_PATH)
        with open(os.path.join(self.EXPORT_IMGS_PATH, self.DUMP_MASKS_SPLINES_FILENAME), "w") as outfile:
            json.dump(dump, outfile)
        print("Mask splines dumped!")

    def load_mask_splines(self):
        path = os.path.join(self.EXPORT_IMGS_PATH, self.DUMP_MASKS_SPLINES_FILENAME)
        if not os.path.isfile(path):
            print("No masks to load")
            return

        with open(path, "r") as infile:
            data = json.load(infile)
        self.n = data['n']
        self.h = data['h']
        self.w = data['w']
        self.scaling = data['scaling']
        self.masks = []
        for spline_dump in data['masks']:
            if spline_dump is None:
                spline = None
            else:
                spline = ClosedSpline(load_from=spline_dump)
            self.masks.append(spline)
        self.handle_scaling_mismatch()
        self.check_shape(self.arch_handler.side_volume.get().shape)
        print('Mask splines loaded!')

    def handle_scaling_mismatch(self):
        if self.scaling != self.arch_handler.side_volume_scale:
            show_message_box("warning", "Scaling mismatch",
                             "The size scale of the volume from which the annotations were taken does not match the current scale. The annotations will be resized and may lose consistency.")
            LoadingDialog(self.rescale_annotations, "Rescaling splines")

    def rescale_annotations(self):
        new_masks = []
        rescale_factor = self.arch_handler.side_volume_scale / self.scaling
        for spline in self.masks:
            if spline is not None:
                coords = [tuple(map(lambda x: int(x * rescale_factor), point)) for point in spline.get_spline()]
                new_spline = ClosedSpline(coords=coords, num_cp=(len(coords) // int(self.NUM_CP_LOSS * rescale_factor)))
                new_masks.append(new_spline)
            else:
                new_masks.append(None)
        self.masks = new_masks
