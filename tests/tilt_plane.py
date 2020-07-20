from Jaw import Jaw
from mayavi import mlab
import numpy as np
import viewer
import processing
from Plane import Plane


if __name__ == "__main__":
    """
    create a plane for cutting and tilt it on the Z axis, show results 
    """
    jaw = Jaw(r'C:\Users\marco\Desktop\3D_ann_dicom\DICOMDIR')

    slice = jaw.get_slice(75)
    p, start, end = processing.arch_detection(slice)
    l_offset, coords, h_offset, derivative = processing.arch_lines(p, start, end)
    side_coords = processing.generate_side_coords(h_offset, l_offset, derivative)

    side_coord = side_coords[50]

    plane = Plane(jaw.Z, len(side_coord))
    plane.from_line(side_coord)

    debug_plane = np.zeros((jaw.Z, jaw.H, jaw.W))
    debug_plane[plane[2].astype(np.int), plane[1].astype(np.int), plane[0].astype(np.int)] = 1

    origin = np.zeros((jaw.Z, jaw.H, jaw.W))
    origin[0:100, 0, 0] = 1
    origin[0, 0, 0:100] = 1
    origin[0, 0:100, 0] = 1

    th = jaw.get_volume()
    th[th < 0.2] = 0

    plane.tilt_x(30)
    # plane.tilt_z(30)

    rotated_plane = np.zeros((jaw.Z, jaw.H, jaw.W))
    rotated_plane[plane[2].astype(np.int), plane[1].astype(np.int), plane[0].astype(np.int)] = 1

    mlab.contour3d(th, color=(1, 1, 1), opacity=0.2)
    mlab.contour3d(jaw.get_gt_volume(), color=(1, 0, 0))
    mlab.contour3d(debug_plane, color=(0, 0, 1))
    mlab.contour3d(rotated_plane, color=(0, 0, 1))
    mlab.contour3d(origin, color=(0, 0, 0))
    mlab.show()

    res = jaw.plane_slice(plane, interp_fn='bicubic_interpolation_3d')
    viewer.plot_2D(res)

