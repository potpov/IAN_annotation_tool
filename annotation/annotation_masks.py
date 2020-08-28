import json
import os
import numpy as np
from annotation.spline.spline import ClosedSpline
from annotation.utils import export_img

EXPORT_IMGS_PATH = os.path.join(os.path.abspath(os.path.curdir), "masks")
EXPORT_IMGS_FILENAME = "_mask.jpg"
DUMP_MASKS_SPLINES_FILENAME = "masks_splines_dump.json"


class AnnotationMasks():

    def __init__(self, shape):
        self.n, self.h, self.w, _ = shape
        self.masks = [None] * self.n
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

    def set_mask_spline(self, idx, spline):
        self.edited = True
        self.masks[idx] = spline

    def get_mask_spline(self, idx):
        return self.masks[idx]

    def get_masks_count(self):
        return len(list(filter(lambda x: x is not None, self.masks)))

    def export_mask_images(self, without_blanks=False):
        if self.mask_volume is None or self.edited:
            self.compute_mask_volume(without_blanks)
        for i, img in enumerate(self.mask_volume):
            filename = "{}{}".format(EXPORT_IMGS_FILENAME, i)
            export_img(img, os.path.join(EXPORT_IMGS_PATH, filename))
        self.edited = False

    def export_mask_splines(self):
        dump = {
            'n': self.n,
            'h': self.h,
            'w': self.w,
            'masks': [
                mask.get_json()
                for mask in self.masks
            ]
        }
        with open(os.path.join(EXPORT_IMGS_PATH, DUMP_MASKS_SPLINES_FILENAME), "w") as outfile:
            json.dump(dump, outfile)
        print("masks splines dumped!")

    def load_mask_splines(self):
        path = os.path.join(EXPORT_IMGS_PATH, DUMP_MASKS_SPLINES_FILENAME)
        if not os.path.isfile(path):
            print("Nothing to load")
            return

        with open(path, "r") as infile:
            data = json.load(infile)
            self.n = data['n']
            self.h = data['h']
            self.w = data['w']
            self.masks = []
            for spline_dump in data['masks']:
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
