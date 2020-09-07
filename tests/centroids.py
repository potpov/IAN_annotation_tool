import viewer
from Jaw import Jaw
from conf import conf
import processing
from Plane import Plane
import numpy as np
from mayavi import mlab
import imageio
from tqdm import tqdm
import cv2

CUT_SLICE_NUM = 96

if __name__ == "__main__":
    """
    in this code we test the computation of centroids, the diff angle and we correct the cutting plane accordingly.
    for simplicity we are going to cut over an annotated volume
    """
    jaw = Jaw(r'C:\Users\marco\Desktop\3D_ann_dicom\DICOMDIR')

    section = jaw.get_slice(CUT_SLICE_NUM)
    p, start, end = processing.arch_detection(section)

    # get the coords of the spline + 2 offset curves
    l_offset, coords, h_offset, derivative = processing.arch_lines(p, start, end)

    # generating orthogonal lines to certthe offsets curves
    side_coords = processing.generate_side_coords(h_offset, l_offset, derivative)
    next_plane = Plane(plane_z=jaw.Z, plane_w=len(side_coords[0]))
    prev_plane = Plane(plane_z=jaw.Z, plane_w=len(side_coords[0]))

    corr_angle = {
        'z': 0,
        'x': 0
    }
    start = 120
    end = 140
    step = 10
    prev_plane.from_line(side_coords[start])
    prev_pred = jaw.plane_slice(prev_plane, cut_gt=True)
    for num_slice in range(start + step, end, step):
        next_plane.from_line(side_coords[num_slice])
        # correction of the angles
        if corr_angle['z'] != 0:
            next_plane.tilt_z(corr_angle['z'])
        if corr_angle['x'] != 0:
            next_plane.tilt_x(next_plane['x'])

        next_pred = jaw.plane_slice(next_plane, cut_gt=True)
        z, x = processing.angle_from_centroids(prev_pred, next_pred, prev_plane, next_plane)

        # updating values
        corr_angle = {
            'z': z,
            'x': x
        }
        prev_pred = next_plane
