import numpy as np
from conf import conf
import processing
from dataloader import load_dicom

"""
THIS SCRIPT CUT THE VOLUME AND CREATE A RECAP GIF OF THE CUT WITH THE POSITION OF THE GT
"""
def lateral_2d_annotation():

    # loading the data
    metadata, volume = load_dicom(conf.DICOM_DIR)

    # Z-axis has to be flipped
    volume = np.flip(volume, 0)

    # remove peak values
    volume = processing.quantiles(volume, min=0, max=0.995)

    # normalize volume between 0 and 1
    volume = processing.simple_normalization(volume)

    # create volume of annotations
    gt_volume = processing.get_annotated_volume(metadata)
    gt_volume = np.flip(gt_volume, 0)

    # choosing a slice and execute dental arch detection
    section = volume[96]
    p, start, end = processing.arch_detection(section)

    # get the coords of the spline + 2 offset curves
    l_offset, coords, h_offset, derivative = processing.arch_lines(p, start, end)
    # generating orthogonal lines to the offsets curves
    side_coords = processing.generate_side_coords(h_offset, l_offset, derivative)
    # volume of sections of the orthogonal lines
    side_volume = processing.canal_slice(volume, side_coords)

    # building an RGB 3D volume with annotations
    gt_drawn = np.tile(volume, (3, 1, 1, 1))  # overlay on the original image (colorful)
    gt_drawn = np.moveaxis(gt_drawn, 0, -1)
    gt_coords = np.argwhere(gt_volume)
    for i in range(gt_coords.shape[0]):
        z, y, x = gt_coords[i]
        gt_drawn[z, y, x] = (1, 0, 0)

    # extracting the side reprojection from this ground truth volume
    side_gt_volume = processing.canal_slice(gt_drawn, side_coords)

    processing.recap_on_gif(coords, h_offset, l_offset, side_volume, side_coords, section, side_gt_volume)
