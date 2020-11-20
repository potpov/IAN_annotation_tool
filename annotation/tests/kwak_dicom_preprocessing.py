from Jaw import Jaw
import cv2
import numpy as np
from skimage.filters import threshold_multiotsu


def plot3d(volume, title=""):
    from mayavi import mlab
    mlab.figure(title)
    mlab.contour3d(volume, contours=8)
    mlab.show()


if __name__ == '__main__':
    dicomdir = r'C:\Users\crime\Desktop\test_dataset\PAZIENTE_7\DICOMDIR'
    jaw = Jaw(dicomdir)
    jaw.rescale(0.5)
    plot3d(jaw.volume, "volume")

    ## STEP A: get central one-third of the volume
    # for our data, we need to get the higher part
    print("Step A")
    volume_z = jaw.Z // 2
    center = jaw.volume[:volume_z]
    plot3d(center, "A")
    thresholds = threshold_multiotsu(center, classes=5)

    ## STEP B: binarization with theeth threshold
    print("Step B")
    theeth_th = cv2.threshold(center, thresholds[3], 1, cv2.THRESH_BINARY)[1].astype(np.uint8)
    plot3d(theeth_th, "B")

    ## STEP C: dilation
    print("Step C")
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated = cv2.morphologyEx(theeth_th, cv2.MORPH_DILATE, kernel)
    plot3d(dilated, "C")

    ## STEP D: confine to tooth height
    print("Step D")
    z_, _, _ = np.where(dilated != 0)
    confined = center[min(z_):max(z_) + 1, :, :]
    plot3d(confined, "D")

    ## STEP E: bone threshold
    print("Step E")
    bone_th = cv2.threshold(confined, thresholds[2], 1, cv2.THRESH_BINARY)[1].astype(np.uint8)
    plot3d(bone_th, "E")

    ## STEP F: complement
    print("Step F")
    complement = bone_th * -1 + 1
    plot3d(complement, "F")

    ## STEP G: combine F with C
    print("Step G")
    tmp = np.zeros_like(complement)
    tmp[min(z_):max(z_) + 1, :, :] = complement
    combineFC = np.bitwise_or(dilated.astype(np.uint8), tmp.astype(np.uint8))
    # plot3d(combineFC)
    original_dims_FC = np.zeros_like(jaw.volume, dtype=np.uint8)
    original_dims_FC[:volume_z] = combineFC
    plot3d(original_dims_FC, "G")

    ## STEP H: extend to the top
    print("Step H")
    # skip

    ## STEP I: inverse
    mask = original_dims_FC * -1 + 1
    plot3d(mask, "I")

    v = jaw.volume * mask
    plot3d(v, "final")
