import numpy as np
import pyecvl._core.ecvl as ecvl
from conf import conf
import glob
import os.path
import viewer
import processing
from dataloader import load_dicom
import cv2
from mayavi import mlab


def lateral_3d_annotation():

    # loading the data
    metadata, volume = load_dicom(conf.DICOM_DIR)

    # Z-axis has to be flipped
    volume = np.flip(volume, 0)

    # remove peak values
    volume = processing.quantiles(volume, min=0, max=0.995)

    # normalize volume between 0 and 1
    volume = processing.simple_normalization(volume)

    # creating RGB volume from volume
    # volume = np.tile(volume, (3, 1, 1, 1))  # overlay on the original image (colorful)
    # volume = np.moveaxis(volume, 0, -1)

    # loading previous side cuts and coords
    side_volume = np.load('side.npy')
    side_coords = np.load('coords.npy', allow_pickle=True)

    # create a volume with the canal annotations stacked
    canal = np.zeros_like(side_volume)
    for i in range(canal.shape[0]):
        mask = cv2.imread(os.path.join(conf.SAVE_DIR, '{}_map.jpg'.format(i)))
        if mask is None:
            continue
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        mask[mask < 125] = 0
        mask[mask > 0] = 1
        mask = mask.astype(np.bool_)
        canal[i, mask] = 1

    # copy previous volume to a jawbone shaped empty volume to reshape the canal correctly
    gt_volume = np.zeros_like(volume)
    for z_id, points in enumerate(side_coords):
        for w_id, (x, y) in enumerate(points):
            gt_volume[:, int(y), int(x)] = canal[z_id, :, w_id]

    # np.save('dataset/gt_volume.npy', gt_volume)
    # np.save('dataset/volume.npy', volume)

    gt_volume = viewer.delaunay(gt_volume)
    viewer.slice_volume(gt_volume)

    # DEBUG #

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
    side_gt_volume = processing.canal_slice(gt_drawn, side_coords)

    processing.recap_on_gif(coords, h_offset, l_offset, side_volume, side_coords, section, side_gt_volume)
