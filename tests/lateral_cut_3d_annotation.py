import numpy as np
import pyecvl._core.ecvl as ecvl
from conf import conf
import glob
import os.path
import viewer
import processing
from dataloader import load_dicom
import cv2


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

    # creating RGB volume from the side volume
    # side_volume = np.tile(side_volume, (3, 1, 1, 1))
    # side_volume = np.moveaxis(side_volume, 0, -1)

    # load annotation for each side slice if it exists
    for i in range(side_volume.shape[0]):
        mask = cv2.imread(os.path.join(conf.SAVE_DIR, '{}_map.jpg'.format(i)))
        if mask is None:
            continue
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        mask[mask < 125] = 0
        mask[mask > 0] = 1
        mask = mask.astype(np.bool_)
        side_volume[i, mask] = 1

    # merging the slices on the original volume
    for z_id, points in enumerate(side_coords):
        for w_id, (x, y) in enumerate(points):
            volume[:, int(y), int(x)] = side_volume[z_id, :, w_id]

    # volume[volume!=1] = 0
    # viewer.plot_3D(volume, vmax=1)

    # merging the slices on an empty volume
    just_canal_side = np.zeros_like(side_volume)
    for i in range(just_canal_side.shape[0]):
        mask = cv2.imread(os.path.join(conf.SAVE_DIR, '{}_map.jpg'.format(i)))
        if mask is None:
            continue
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        mask[mask < 125] = 0
        mask[mask > 0] = 1
        mask = mask.astype(np.bool_)
        just_canal_side[i, mask] = 1

    just_canal = np.zeros_like(volume)
    for z_id, points in enumerate(side_coords):
        for w_id, (x, y) in enumerate(points):
            just_canal[:, int(y), int(x)] = just_canal_side[z_id, :, w_id]
    # viewer.plot_3D(just_canal)
    viewer.delaunay(just_canal)

    # processing.recap_on_gif(coords, h_offset, l_offset, side_volume, side_coords, section, side_gt_volume)
