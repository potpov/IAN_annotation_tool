import numpy as np
import pyecvl._core.ecvl as ecvl
from conf import conf
import glob
import os.path
import viewer
import processing
from dataloader import load_dicom
import cv2
from skimage.segmentation import active_contour


def expand_2d_annotation():
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

    # choosing a slice and execute dental arch detection
    section = volume[96]
    p, start, end = processing.arch_detection(section)

    # get the coords of the spline + 2 offset curves
    l_offset, coords, h_offset, derivative = processing.arch_lines(p, start, end)
    # generating orthogonal lines to the offsets curves
    side_coords = processing.generate_side_coords(h_offset, l_offset, derivative)
    # volume of sections of the orthogonal lines
    side_volume = processing.canal_slice(volume, side_coords)

    # building an RGB 3D volume with annotations
    gt_drawn = np.tile(volume, (3, 1, 1, 1))  # overlay on the original image (colorful)
    gt_drawn = np.moveaxis(gt_drawn, 0, -1)
    gt_coords = np.argwhere(gt_volume)
    for i in range(gt_coords.shape[0]):
        z, y, x = gt_coords[i]
        gt_drawn[z, y, x] = (1, 0, 0)

    # extracting the side reprojection from this ground truth volume
    side_gt_volume, _ = processing.canal_slice(gt_drawn, side_coords)

    slice_num = 70

    indices = np.where(np.all(side_gt_volume[slice_num] == (1, 0, 0), axis=-1))

    viewer.plot_2D(side_gt_volume[slice_num])

    result = side_volume[slice_num].copy()
    result = cv2.normalize(result, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    x, y = indices[1][0], indices[0][0]

    # creting the circle around the zone
    s = np.linspace(0, 2 * np.pi, 400)
    radius = 5
    r = x + radius * np.sin(s)
    c = y + radius * np.cos(s)
    init = np.array([r, c]).T

    # showing the circle
    tmp = result.copy()
    for x, y in init:
        if x > result.shape[1] or y > result.shape[0]:
            continue
        tmp[int(y), int(x)] = 255
    viewer.plot_2D(tmp)

    # searching
    snake = active_contour(
        result,
        init,
        alpha=10,
        beta=10,
        gamma=0.001,
        w_line=-5,
        w_edge=5
    )

    # print
    for x, y in snake:
        if x > result.shape[1] or y > result.shape[0]:
            continue
        result[int(y), int(x)] = 255

    viewer.plot_2D(result)

    # END TEST!
