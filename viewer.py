import os
from matplotlib import pyplot as plt
from matplotlib.tri import Triangulation, TriAnalyzer, UniformTriRefiner

if "REMOTE" not in os.environ:
    from mayavi import mlab

import numpy as np
import cv2
from scipy.spatial import Delaunay
from scipy import spatial as sp_spatial
from Plane import Plane
from voxelize.voxelize import voxelize
from sklearn.metrics import mean_squared_error as mse
import imageio


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


def plot_2D(dicom_slice, cmap="gray", title=""):
    plt.title(title)
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


def annotated_volume(volume, ann_volume):
    th = volume.copy()
    th[th < 0.2] = 0
    mlab.contour3d(th, color=(1, 1, 1), opacity=0.2)
    mlab.contour3d(ann_volume, color=(1, 0, 0))
    mlab.show()


def recap_on_gif(coords, high_offset, low_offset, side_volume, side_coords, slice, gt_side_volume):
    """
    create a gif recap where a panoramic of the cross cuts is visible along with the section and the ground truth
    :param coords: set of coords of the dental line (for drawing)
    :param high_offset: set of coords of the first offset from coords (for drawing)
    :param low_offset: set of coords of the second offset from coords (for drawing)
    :param side_volume: 3D volume of the cuts
    :param side_coords: coords of the lines we used to cut and generate side_volume
    :param slice: 2D image where coords and offsets are drawn
    :param gt_side_volume: RGB 4D volume, same of side_volume but with annotations
    :return: a gif
    """

    slice = cv2.normalize(slice, slice, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    original = np.tile(slice, (3, 1, 1))  # overlay on the original image (colorful)
    original = np.moveaxis(original, 0, -1)

    # drawing the line and the offsets of the upper view
    for idx in range(len(coords)):
        original[int(coords[idx][1]), int(coords[idx][0])] = (255, 0, 0)
        try:
            original[int(high_offset[idx][1]), int(high_offset[idx][0])] = (0, 255, 0)
            original[int(low_offset[idx][1]), int(low_offset[idx][0])] = (0, 255, 0)
        except:
            continue
    # create an upper view for each section
    sections = []
    for points in side_coords:
        tmp = original.copy()
        for x, y in points:
            if slice.shape[1] > x > 0 and slice.shape[0] > y > 0:
                tmp[int(y), int(x)] = (0, 0, 255)
        sections.append(tmp)
    sections = np.stack(sections)

    # rescaling the projection volume properly
    y_ratio = original.shape[0] / side_volume.shape[1]
    width = int(side_volume.shape[2] * y_ratio)
    height = int(side_volume.shape[1] * y_ratio)
    scaled_side_volume = np.ndarray(shape=(side_volume.shape[0], height, width))
    scaled_gt_volume = np.ndarray(shape=(gt_side_volume.shape[0], height, width, 3))
    for i in range(side_volume.shape[0]):
        scaled_side_volume[i] = cv2.resize(side_volume[i, :, :], (width, height), interpolation=cv2.INTER_AREA)
        scaled_gt_volume[i] = cv2.resize(gt_side_volume[i, :, :], (width, height), interpolation=cv2.INTER_AREA)

    # padding the side volume and rescaling
    # pad_side_volume = np.zeros((side_volume.shape[0], original.shape[0], original.shape[1]))
    # pad_side_volume[:, :side_volume.shape[1], :side_volume.shape[2]] = side_volume
    scaled_side_volume = cv2.normalize(scaled_side_volume, scaled_side_volume, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    scaled_gt_volume = cv2.normalize(scaled_gt_volume, scaled_gt_volume, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # creating RGB volume
    scaled_side_volume = np.tile(scaled_side_volume, (3, 1, 1, 1))  # overlay on the original image (colorful)
    scaled_side_volume = np.moveaxis(scaled_side_volume, 0, -1)

    # GIF creation
    gif_source = np.concatenate((sections, scaled_side_volume, scaled_gt_volume), axis=2)
    gif = []
    for i in range(gif_source.shape[0]):
        gif.append(gif_source[i, :, :])
    imageio.mimsave('test.gif', gif)


def show_planes(main_volume, other_volumes):
    """
    show an arbitrary list of volumes
    Args:
        main_volume (numpy array): numpy volume
        other_volumes (List): list of numpy volumes
    """

    if type(other_volumes) != list:
        raise Exception("other_volumes must be a list of volumes! please bound your volumes within brackets")

    mlab.contour3d(main_volume, color=(1, 1, 1), opacity=.2)

    colors = np.random.rand(len(main_volume), 3)
    for idx, volume in enumerate(other_volumes):
        # handle plane objects
        if type(volume) == Plane:
            plane = volume.get_plane()
            volume = np.zeros_like(main_volume)
            volume[
                plane[2].astype(np.int),
                plane[1].astype(np.int),
                plane[0].astype(np.int)
            ] = 1
        mlab.contour3d(volume, color=tuple(colors[idx]))

    origin = np.zeros_like(main_volume)
    origin[0:100, 0, 0] = 1
    origin[0, 0, 0:100] = 1
    origin[0, 0:100, 0] = 1
    mlab.contour3d(origin, color=(0, 0, 0))

    mlab.show()
