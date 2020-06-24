import numpy as np
from conf import conf
import processing
from dataloader import load_dicom
import cv2


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
    l_offset, coords, h_offset, derivative = processing.arch_lines(p, start, end, offset=2)

    # generating panorex
    panorex = processing.create_panorex(volume, coords, h_offset, l_offset)
    panorex = cv2.normalize(panorex, panorex, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    cv2.imwrite(r'Y:\work\datasets\canal_segmentation\patient1\panorex\panorex.jpg', panorex)


if __name__ == "__main__":
    panorex_creation()