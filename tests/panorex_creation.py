import numpy as np
from conf import conf
import processing
import viewer
import cv2
from Jaw import Jaw


def panorex_creation():
    """
    Detect dental arch, create panorex
    """

    jaw = Jaw(conf.DICOM_DIR)

    section = jaw.get_slice(96)
    p, start, end = processing.arch_detection(section)

    # get the coords of the spline + 2 offset curves
    l_offset, coords, h_offset, derivative = processing.arch_lines(p, start, end, offset=5)

    panorex = jaw.create_panorex(h_offset)
    # generating panorex

    panorex = cv2.normalize(panorex, panorex, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    viewer.plot_2D(panorex)
    cv2.imwrite(r'Y:\work\datasets\canal_segmentation\patient1\panorex\panorex.jpg', panorex)


if __name__ == "__main__":
    panorex_creation()