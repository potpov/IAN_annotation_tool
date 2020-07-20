import numpy as np
import processing
from Jaw import Jaw


def create_dataset():
    """
    creating a dataset for the neural network
    load 3D volumes (data and annotations), create many 2D sets of cuts (data and annotation)
    if annotations are not available a black set of masks get returned
    augmentation to be added yet
    """

    jaw = Jaw(r'C:\Users\marco\Desktop\3D_ann_dicom\DICOMDIR')

    idxs = [96, 120, 130]
    offset = 50

    # TODO: the first element has to be removed or will be a black mask
    side_volume = np.zeros(shape=(1, jaw.Z, 2 * offset + 1))
    gt_side_volume = np.zeros(shape=(1, jaw.Z, 2 * offset + 1))

    for idx in idxs:
        section = jaw.get_slice(idx)
        p, start, end = processing.arch_detection(section, debug=False)

        # get the coords of the spline + 2 offset curves
        l_offset, coords, h_offset, derivative = processing.arch_lines(p, start, end, offset=offset)

        # generating orthogonal lines to the offsets curves
        side_coords = processing.generate_side_coords(h_offset, l_offset, derivative, offset=2*offset)

        side_volume = np.append(
            side_volume,
            jaw.line_slice(side_coords),
            axis=0
        )
        gt_side_volume = np.append(
            gt_side_volume,
            jaw.line_slice(side_coords, cut_gt=True),
            axis=0
        )

    for i in range(side_volume.shape[0]):
        side_volume[i] = processing.increase_contrast(side_volume[i])

    np.save(r'Y:\work\datasets\canal_segmentation\patient1\slices\data.npy', side_volume)
    np.save(r'Y:\work\datasets\canal_segmentation\patient1\slices\gt.npy', gt_side_volume)


if __name__ == "__main__":
    create_dataset()
