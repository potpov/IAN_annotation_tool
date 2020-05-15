import numpy as np
import pyecvl._core.ecvl as ecvl
from conf import conf
import glob
import os.path
import viewer
import processing
from dataloader import load_dicom
# from dataloader import load_from_path
import cv2


def main():

    # loading the data
    metadata, volume = load_dicom(conf.DICOM_DIR)

    # Z-axis has to be flipped
    volume = np.flip(volume, 0)

    # choosing a slice for dental arch detection
    slice = volume[96]
    slice = processing.simple_normalization(slice)
    p, start, end = processing.arch_detection(slice)

    # re-projecting the jawbone from the dental line
    proj = processing.spline_projection(volume, func=p, start=start, end=end)

    return

    # EX: obtain the annotations and draw them
    metadata, volume = load_dicom(conf.DICOM_DIR)
    meta_slice = metadata[45]
    data_slice = volume[45]
    annotations = processing.get_annotations(meta_slice)
    viewer.draw_annotation(data_slice, annotations)

    # dicom files are reversely ordered
    # volume = np.flip(volume, 0)

    # cutting the file along the y axis
    # projection = processing.y_slice(volume, 60)
    # viewer.plot_2D(projection)


if __name__ == "__main__":
    main()
