import numpy as np
from conf import conf
import processing
from dataloader import load_dicom


def panorex_creation():
    """
    stack DICOM files together, detect dental arch, create panorex
    """

    # loading the data
    metadata, volume = load_dicom(conf.DICOM_DIR)

    # Z-axis has to be flipped
    volume = np.flip(volume, 0)

    # remove peak values
    volume = processing.quantiles(volume, min=0, max=0.995)

    # normalize volume between 0 and 1
    volume = processing.simple_normalization(volume)

    # choosing a slice and execute dental arch detection
    section = volume[96]
    p, start, end = processing.arch_detection(section)

    # get the coords of the spline + 2 offset curves
    l_offset, coords, h_offset, derivative = processing.arch_lines(p, start, end, offset=5)

    # generating panorex
    panorex = processing.create_panorex(volume, coords, h_offset, l_offset)


if __name__ == "__main__":
    panorex_creation()