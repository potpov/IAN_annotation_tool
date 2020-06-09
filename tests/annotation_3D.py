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


def annotation_3D():
    """
    load 2D annotation, stack them and create a 3D canal volume
    """

    # loading the data
    metadata, volume = load_dicom(conf.DICOM_DIR)

    # Z-axis has to be flipped
    volume = np.flip(volume, 0)

    # remove peak values
    volume = processing.quantiles(volume, min=0, max=0.995)

    # normalize volume between 0 and 1
    volume = processing.simple_normalization(volume)

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

    # smoothing surface
    gt_volume = viewer.delaunay(gt_volume)
    viewer.plot_3D(gt_volume)


if __name__ == "__main__":
    annotation_3D()