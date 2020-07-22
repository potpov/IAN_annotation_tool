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
    plane.from_line(side_coord)  # load the plane from a line

    debug_start_plane = np.zeros((jaw.Z, jaw.H, jaw.W))
    debug_start_plane[plane[2].astype(np.int), plane[1].astype(np.int), plane[0].astype(np.int)] = 1

    start_plane = plane.get_plane()
    plane.tilt_x(30)
    plane.tilt_z(30)

    # new rotated plane
    debug_rotated_plane = np.zeros((jaw.Z, jaw.H, jaw.W))
    debug_rotated_plane[plane[2].astype(np.int), plane[1].astype(np.int), plane[0].astype(np.int)] = 1

    plane.set_plane(start_plane)
    plane.tilt_z(30)
    plane.tilt_x(30)

    # new rotated plane
    debug_rotated_plane_reverse = np.zeros((jaw.Z, jaw.H, jaw.W))
    debug_rotated_plane_reverse[plane[2].astype(np.int), plane[1].astype(np.int), plane[0].astype(np.int)] = 1

    viewer.show_planes(jaw.get_volume(), [jaw.get_gt_volume(), debug_start_plane, debug_rotated_plane, debug_rotated_plane_reverse])

    # res = jaw.plane_slice(plane, interp_fn='bicubic_interpolation_3d')
    # viewer.plot_2D(res)



