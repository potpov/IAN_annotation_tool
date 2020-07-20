import numpy as np
from conf import conf
import processing
from Jaw import Jaw
import viewer


def annotation_2D():
    """
    dental arch detection, volume lateral cut, recap of the cuts along with the ground truth on a gif
    """

    jaw = Jaw(conf.DICOM_DIR)

    # choosing a slice and execute dental arch detection
    # patient [2, 7] -> slice num 96
    # patient [1] -> slice num ?
    # patient [4] -> slice num 75
    section = jaw.get_slice(96)
    p, start, end = processing.arch_detection(section, debug=True)

    # get the coords of the spline + 2 offset curves
    l_offset, coords, h_offset, derivative = processing.arch_lines(p, start, end)

    # generating orthogonal lines to the offsets curves
    side_coords = processing.generate_side_coords(h_offset, l_offset, derivative)

    # volume of sections of the orthogonal lines
    side_volume = jaw.line_slice(side_coords)
    # gt_volume = jaw.line_slice(side_coords, cut_gt=True)

    # building an RGB 3D volume with annotations marked as red
    gt_drawn = np.tile(jaw.get_volume(), (3, 1, 1, 1))  # overlay on the original image (colorful)
    gt_drawn = np.moveaxis(gt_drawn, 0, -1)
    gt_coords = np.argwhere(jaw.get_gt_volume())
    for i in range(gt_coords.shape[0]):
        z, y, x = gt_coords[i]
        gt_drawn[z, y, x] = (1, 0, 0)

    # 4D slicing with an RGB volume -> not implemented in class Jaw
    side_gt_volume = np.zeros((len(side_coords), jaw.Z, len(side_coords[0]), 3), np.float32)
    for z_id, points in enumerate(side_coords):
        for w_id, (x, y) in enumerate(points):
            # avoiding overflow
            if (x - 2) < 0 or (y - 2) < 0 or (x + 2) >= jaw.W or (y + 2) >= jaw.H:
                side_gt_volume[z_id, :, w_id, :] = np.zeros(shape=(jaw.Z, 3))  # fill the array with zeros
            else:
                side_gt_volume[z_id, :, w_id, :] = gt_drawn[:, int(y), int(x)]  # bilinear interpolation

    viewer.recap_on_gif(coords, h_offset, l_offset, side_volume, side_coords, section, side_gt_volume)


if __name__ == "__main__":
    annotation_2D()
