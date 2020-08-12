import numpy as np
from conf import conf
import processing
import viewer
import cv2
from Jaw import Jaw


def enhance_contrast(img):
    # CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=3., tileGridSize=(8, 8))

    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)  # convert from BGR to LAB color space
    l, a, b = cv2.split(lab)  # split on 3 different channels

    l2 = clahe.apply(l)  # apply CLAHE to the L-channel

    lab = cv2.merge((l2, a, b))  # merge channels
    img2 = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)  # convert from LAB to BGR

    return img2


def panorex_creation():
    """
    Detect dental arch, create panorex
    """
    panorex = cv2.imread(r"C:\Users\crime\Desktop\alveolar_nerve/dataset/panorex_imgs/panorex7.jpg")
    original = np.copy(panorex)
    # viewer.plot_2D(panorex)

    # contrast
    panorex = enhance_contrast(panorex)
    viewer.plot_2D(panorex)

    # smoothing
    panorex = cv2.bilateralFilter(panorex, 50, 150, 75)
    viewer.plot_2D(panorex)

    # edge detection
    panorex = cv2.Canny(panorex, 20, 150)
    viewer.plot_2D(panorex)

    # distance transform
    panorex = cv2.bitwise_not(panorex)
    panorex = cv2.distanceTransform(panorex, cv2.DIST_L1, 3)
    panorex = cv2.normalize(panorex, panorex, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    viewer.plot_2D(panorex)

    # thresh
    panorex = cv2.adaptiveThreshold(panorex, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)
    viewer.plot_2D(panorex)

    # opening
    kernel = np.ones((3, 3))
    panorex = cv2.morphologyEx(panorex, cv2.MORPH_OPEN, kernel)
    viewer.plot_2D(panorex)

    # closing
    l_kernel = np.array([[1, 0, 0],
                         [0, 1, 0],
                         [0, 0, 1]]).astype(np.uint8)
    r_kernel = np.array([[0, 0, 1],
                         [0, 1, 0],
                         [1, 0, 0]]).astype(np.uint8)
    mid_val = panorex.shape[1] // 2
    panorex[:, :mid_val] = cv2.morphologyEx(panorex[:, :mid_val], cv2.MORPH_CLOSE, l_kernel)
    panorex[:, mid_val:] = cv2.morphologyEx(panorex[:, mid_val:], cv2.MORPH_CLOSE, r_kernel)
    viewer.plot_2D(panorex)

    # ccl
    ret, labels = cv2.connectedComponents(panorex)
    for label in range(1, ret):
        mask = np.array(labels, dtype=np.uint8)
        mask[labels == label] = 255
        cv2.imshow('component', mask)
        cv2.waitKey(0)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    panorex_creation()
