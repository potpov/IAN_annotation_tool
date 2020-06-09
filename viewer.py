from matplotlib import pyplot as plt
from matplotlib.tri import Triangulation, TriAnalyzer, UniformTriRefiner
from mayavi import mlab
import numpy as np
import cv2
from scipy.spatial import Delaunay
from scipy import spatial as sp_spatial
import mpl_toolkits.mplot3d as a3
import matplotlib as mpl
import scipy as sp
import cc3d
from voxelize.voxelize import voxelize
from sklearn.metrics import mean_squared_error as mse


def slice_volume(volume):
    # 2D slicing
    mlab.volume_slice(volume, plane_orientation='x_axes')
    mlab.show()


def plot_3D(volume, vmin=0, vmax=255, name='yet another scene'):
    mlab.contour3d(volume, vmin=vmin, vmax=vmax, name=name)
    mlab.show()


def delaunay(volume):

    coords = np.argwhere(volume == 1)

    min_z, min_y, min_x = coords[:, 0].min(), coords[:, 1].min(), coords[:, 2].min()
    max_z, max_y, max_x = coords[:, 0].max(), coords[:, 1].max(), coords[:, 2].max()

    kernel_size = 22
    stride = 18
    th = 9000

    smooth_vol = np.zeros_like(volume)

    z_start = min_z
    while z_start < max_z:
        y_start = min_y
        while y_start < max_y:
            x_start = min_x
            while x_start < max_x:

                v = coords[
                    (coords[:, 1] > y_start) & (coords[:, 1] < y_start + kernel_size) &
                    (coords[:, 0] > z_start) & (coords[:, 0] < z_start + kernel_size) &
                    (coords[:, 2] > x_start) & (coords[:, 2] < x_start + kernel_size)
                    ]

                # meshing is executed if we have at least 3 points
                if v.size < 9:
                    # if v.size > 0:
                    #     smooth_vol[v[:, 0], v[:, 1], v[:, 2]] = 1
                    x_start += stride
                    continue

                # if all the points are on the same plane we make a 2D convex hull
                # while v[:, 0].max() == v[:, 0].min() or v[:, 1].max() == v[:, 1].min() or v[:, 2].max() == v[:, 2].min():
                #     x_start -= momentum
                #     x_end += momentum
                #     y_start -= momentum
                #     y_end += momentum
                #     z_start -= momentum
                #     z_end += momentum
                #     v = coords[
                #         (coords[:, 1] > y_start) & (coords[:, 1] < y_end) &
                #         (coords[:, 0] > z_start) & (coords[:, 0] < z_end) &
                #         (coords[:, 2] > x_start) & (coords[:, 2] < x_end)
                #         ]

                if v[:, 0].max() == v[:, 0].min() or v[:, 1].max() == v[:, 1].min() or v[:, 2].max() == v[:, 2].min():
                    x_start += stride
                    continue

                hull = sp_spatial.ConvexHull(v, incremental=True).simplices
                # mlab.triangular_mesh(v[:, 2], v[:, 1], v[:, 0], hull, color=(0, 1, 0))

                # filtering biggest tringles
                # tri = [v for v in v[hull] if abs(np.linalg.det(v))/2 < th]
                # tri = np.stack(tri)
                tri = v[hull]

                # voxellization
                if tri.size > 0:
                    for z, y, x in voxelize(tri):
                        smooth_vol[z, y, x] = 1
                x_start += stride
            y_start += stride
        z_start += stride

    return smooth_vol


def plot_2D(dicom_slice, cmap="gray"):
    plt.imshow(np.squeeze(dicom_slice), cmap=cmap)
    plt.show()


def draw_annotation(slice, gt_mask):
    if len(slice.shape) == 2:
        # create a RGB version of the image
        dicom = np.tile(slice, (3, 1, 1))
        dicom = np.moveaxis(dicom, 0, -1)
        coords = np.argwhere(gt_mask > 0)
        for coord in coords:
            dicom[coord[0], coord[1], :] = (1, 0, 0)
        # final plot
        plot_2D(dicom)
    else:
        raise Exception("TODO: 3D annotation drawing not implemented yet.")

