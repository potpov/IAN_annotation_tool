import json
import os
import numpy as np
from annotation.spline.spline import ClosedSpline
from annotation.utils import export_img, active_contour_balloon


class AnnotationMasks():
    MASK_DIR = 'masks'
    EXPORT_IMGS_PATH = ""
    EXPORT_IMGS_FILENAME = "_mask.jpg"
    DUMP_MASKS_SPLINES_FILENAME = "masks_splines_dump.json"

    def __init__(self, shape, arch_handler):
        self.n, self.h, self.w, _ = shape
        self.arch_handler = arch_handler
        self.EXPORT_IMGS_PATH = os.path.join(os.path.dirname(self.arch_handler.dicomdir_path), self.MASK_DIR)
        self.masks = [None] * self.n
        self.created_from_snake = [False] * self.n
        self.mask_volume = None
        self.blank_img = np.zeros((self.h, self.w)).astype(np.uint8)
        self.edited = True

    def compute_mask_image(self, spline):
        return spline.generate_mask((self.h, self.w)) if spline is not None else self.blank_img

    def compute_mask_volume(self, without_blanks=False):
        z = self.get_masks_count() if without_blanks else self.n
        masks = list(filter(lambda x: x is not None, self.masks)) if without_blanks else self.masks
        shape = (z, self.h, self.w)
        mask_volume = np.zeros(shape).astype(np.uint8)
        for i, mask in enumerate(masks):
            mask_volume[i, :, :] = self.compute_mask_image(mask)
        self.mask_volume = mask_volume
        return mask_volume

    def set_mask_spline(self, idx, spline, from_snake=False):
        self.edited = True
        self.created_from_snake[idx] = from_snake
        self.masks[idx] = spline
        return spline

    def downscale_spline(self, spline, downscale_factor):
        coords = [tuple(map(lambda x: int(x / downscale_factor), point)) for point in spline.get_spline()]
        return ClosedSpline(coords, len(coords) // (15 // downscale_factor))

    def get_mask_spline(self, idx, from_snake=False, downscale_factor=1):
        if self.masks[idx] is None and from_snake is True:
            init = self.masks[idx - 1] or self.masks[idx + 1]
            if init is not None:
                ####
                ## Approach with skimage.segmentation.active_contour
                # spline = np.array(init.get_spline())
                # snake = active_contour(self.arch_handler.side_volume[idx], spline, max_iterations=100)
                ####
                snake = active_contour_balloon(self.arch_handler.side_volume[idx], init, debug=False)
                if snake is None:
                    return None
                self.set_mask_spline(idx, ClosedSpline(snake, len(snake) // 15), from_snake)

        if self.masks[idx] is not None and downscale_factor != 1:
            return self.downscale_spline(self.masks[idx], downscale_factor)
        return self.masks[idx]

    def get_masks_count(self):
        return len(list(filter(lambda x: x is not None, self.masks)))

    def export_mask_images(self, without_blanks=False):
        if self.mask_volume is None or self.edited:
            self.compute_mask_volume(without_blanks)
        for i, img in enumerate(self.mask_volume):
            filename = "{}{}".format(self.EXPORT_IMGS_FILENAME, i)
            export_img(img, os.path.join(self.EXPORT_IMGS_PATH, filename))
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
        print("masks splines dumped!")

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
            self.masks = []
            for spline_dump in data['masks']:
                if spline_dump is None:
                    spline = None
                else:
                    spline = ClosedSpline([])
                    spline.read_json(spline_dump)
                self.masks.append(spline)

        print('masks splines loaded!')


if __name__ == '__main__':
    am = AnnotationMasks((300, 200, 100, 1))
    am.set_mask_spline(10, ClosedSpline([]))
    print("masks count: {}".format(am.get_masks_count()))
    vwob = am.compute_mask_volume(without_blanks=True)
    print(vwob.shape)
    vwb = am.compute_mask_volume(without_blanks=False)
    print(vwb.shape)
