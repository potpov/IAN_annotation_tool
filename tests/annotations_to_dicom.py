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
from Jaw import Jaw


def annotations_to_dicom():
    """
    load 2D annotations, stack them and create a 3D canal volume, smooth the surface. save the new volume in a DICOMDIR folder!
    """

    jaw = Jaw(conf.DICOM_DIR)

    # loading previous side cuts and coords
    side_volume = np.load(r'Y:\work\datasets\canal_segmentation\patient1\sides\side.npy')
    side_coords = np.load(r'Y:\work\datasets\canal_segmentation\patient1\sides\coords.npy', allow_pickle=True)

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
    gt_volume = np.zeros_like(jaw.get_volume())
    for z_id, points in enumerate(side_coords):
        for w_id, (x, y) in enumerate(points):
            gt_volume[:, int(y), int(x)] = canal[z_id, :, w_id]

    jaw.set_gt_volume(gt_volume)
    jaw.overwrite_annotations()
    jaw.save_dicom(r'C:\Users\marco\Desktop\test_annotation3D\DICOMDIR')

    # TODO: fill the smooth surface after convex hull and save it
    # gt_volume = viewer.delaunay(gt_volume)
    # viewer.plot_3D(gt_volume)


if __name__ == "__main__":
    annotations_to_dicom()