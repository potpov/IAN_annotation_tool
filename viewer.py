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


def slice_volume(volume):
    # 2D slicing
    mlab.volume_slice(volume, plane_orientation='x_axes')
    mlab.show()


def plot_3D(volume, vmin=0, vmax=255, transparent=False):
    mlab.contour3d(volume, vmin=vmin, vmax=vmax, contours=4)
    mlab.show()


def delaunay(volume):

    label_out = cc3d.connected_components(volume.astype(np.bool_))

    # coords of the right canal
    coords = np.argwhere(label_out == 1)

    min_y = coords[:, 1].min()
    max_y = coords[:, 1].max()
    offset = 70

    tri_coords = np.ndarray(shape=(1, 3), dtype=np.int)
    for i in range(max_y // offset):
        vertex_coords = coords[
            (coords[:, 1] > min_y + (offset * i)) &
            (coords[:, 1] < min_y + (offset * (i + 1)))
        ]
        if vertex_coords.size == 0:
            continue

        tri_coords = np.append(
            tri_coords,
            sp_spatial.ConvexHull(vertex_coords, incremental=True).simplices,
            axis=0
        )

    # delaunay method 1
    # z, y, x = coords[:, 0], coords[:, 1], coords[:, 2]
    # source = mlab.points3d(x, y, z, opacity=0.3, mode='2dvertex')
    # launay = mlab.pipeline.delaunay3d(source)
    # edges = mlab.pipeline.extract_edges(launay)
    # mlab.pipeline.surface(edges, opacity=0.3, line_width=3, color=(1, 0, 0))
    # mlab.show()

    # hull = sp_spatial.ConvexHull(coords)
    # surf = coords[hull.simplices]
    surf = coords[tri_coords]

    # filtering
    # thr = np.array([])
    # for v1, v2, v3 in surf:
    #     thr = np.append(
    #         thr,
    #         np.array([np.abs(v1 - v2), np.abs(v2 - v3),np.abs(v3 - v1)]).max()
    #     )
    # thr_coords = np.argwhere(thr.astype(np.int) > 400)

    # voxelising the triangles
    smooth_vol = np.zeros_like(volume)
    for z, y, x in voxelize(surf):
        smooth_vol[z, y, x] = 255

    # plot and return
    plot_3D(smooth_vol)
    input()
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

