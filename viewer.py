from matplotlib import pyplot as plt
from mayavi import mlab
import numpy as np
import cv2


def slice_volume(volume):
    # 2D slicing
    mlab.volume_slice(volume, plane_orientation='x_axes')
    mlab.show()


def plot_3D(volume, vmin=0, vmax=255, transparent=False):
    mlab.contour3d(volume, vmin=vmin, vmax=vmax, contours=4)
    mlab.show()


def plot_2D(dicom_slice, cmap="gray"):
    plt.imshow(np.squeeze(dicom_slice), cmap=cmap)
    plt.show()


def draw_annotation(slice, gt_mask):
    # create a RGB version of the image
    dicom = np.tile(slice, (3, 1, 1))
    dicom = np.moveaxis(dicom, 0, -1)
    coords = np.argwhere(gt_mask > 0)
    for coord in coords:
        dicom[coord[0], coord[1], :] = (1, 0, 0)
    # final plot
    plot_2D(dicom)

