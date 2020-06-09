import numpy as np
import processing
import viewer


def create_dataset():
    volume = np.load('dataset/volume.npy')
    gt_volume = np.load('dataset/gt_volume.npy')
    idxs = [96, 120, 130]

    offset = 50

    side_volume = np.empty(shape=(1, volume.shape[0], 2 * offset + 1))
    gt_side_volume = np.empty(shape=(1, volume.shape[0], 2 * offset + 1))

    for idx in idxs:
        section = volume[idx]

        p, start, end = processing.arch_detection(section)

        # get the coords of the spline + 2 offset curves
        l_offset, coords, h_offset, derivative = processing.arch_lines(p, start, end, offset=offset)

        # generating orthogonal lines to the offsets curves
        side_coords = processing.generate_side_coords(h_offset, l_offset, derivative, offset=2*offset)

        side_volume = np.append(side_volume, processing.canal_slice(volume, side_coords), axis=0)
        gt_side_volume = np.append(gt_side_volume, processing.canal_slice(gt_volume, side_coords), axis=0)

    np.save('dataset/slices/data.npy', side_volume)
    np.save('dataset/slices/gt.npy', gt_side_volume)
    
    return