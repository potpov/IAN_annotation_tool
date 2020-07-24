import processing
from dataloader import load_dicom
from conf import conf
import numpy as np
import cv2

if __name__ == '__main__':
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

    # get the coords of the spline + 2 coords curves
    l_offset, coords, h_offset, derivative = processing.arch_lines(p, start, end)
    # generating orthogonal lines to the offsets curves
    side_coords = processing.generate_side_coords(h_offset, l_offset, derivative)
    # volume of sections of the orthogonal lines
    side_volume = processing.canal_slice(volume, side_coords)

    for i, img in enumerate(side_volume):
        filename = "imgs/{:03d}.png".format(i)
        img = cv2.convertScaleAbs(img, alpha=(255.0))
        print("writing {}".format(filename))
        cv2.imwrite(filename, img)
