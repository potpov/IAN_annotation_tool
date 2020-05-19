import numpy as np
import pyecvl._core.ecvl as ecvl
from conf import conf
import glob
import os.path
import viewer
import processing
from dataloader import load_dicom
import cv2


def main():

    # loading the data
    metadata, volume = load_dicom(conf.DICOM_DIR)

    # Z-axis has to be flipped
    volume = np.flip(volume, 0)

    # remove peak values
    volume = processing.quantiles(volume, min=0, max=0.995)
    # normalize volume between 0 and 1
    volume = processing.simple_normalization(volume)

    # create volume of annotations
    gt_volume = processing.get_annotated_volume(metadata)
    gt_volume = np.flip(gt_volume, 0)

    # choosing a slice for dental arch detection
    slice = volume[96]
    p, start, end = processing.arch_detection(slice, debug=True)

    l_offset, coords, h_offset, derivative = processing.arch_lines(p, start, end)
    side_volume, side_slices_coords = processing.canal_slice(volume, (h_offset, l_offset), derivative)

    # building an RGB 3D volume with annotations
    gt_drawn = np.tile(volume, (3, 1, 1, 1))  # overlay on the original image (colorful)
    gt_drawn = np.moveaxis(gt_drawn, 0, -1)
    gt_coords = np.argwhere(gt_volume)
    for i in range(gt_coords.shape[0]):
        z, y, x = gt_coords[i]
        gt_drawn[z, y, x] = (1, 0, 0)

    # extracting the side reprojection from this ground truth volume
    side_gt_volume, _ = processing.canal_slice(gt_drawn, (h_offset, l_offset), derivative)

    processing.recap_on_gif(coords, h_offset, l_offset, side_volume, side_slices_coords, volume[97], side_gt_volume)
    return
    # re-projecting the jawbone from the dental line
    panorex = processing.create_panorex(volume, coords, h_offset, l_offset)


if __name__ == "__main__":
    main()
