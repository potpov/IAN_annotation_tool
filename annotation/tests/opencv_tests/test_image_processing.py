import numpy as np
import cv2
import matplotlib.pyplot as plt


def plot(a):
    plt.imshow(a, cmap='gray')
    plt.show()


def show_red_mask(img, mask):
    img_ = img
    mask_ = np.bool_(mask)
    red = img_[:, :, 0]
    green = img_[:, :, 1]
    blue = img_[:, :, 2]
    red[mask_] = 255
    green[mask_] = 0
    blue[mask_] = 0
    return img_


if __name__ == '__main__':
    img = cv2.imread('imgs/100.png')
    img_ = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    plot(img_)

    img_ = cv2.bitwise_not(img_)
    blur = cv2.bilateralFilter(img_, 5, 50, 50)
    # th = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 45, 5)
    # closing = cv2.morphologyEx(th, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

    canny = cv2.Canny(blur, 20, 100)
    plot(canny)

    closed_canny = cv2.morphologyEx(canny, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    plot(closed_canny)

    h, w = img_.shape
    mask = np.zeros((h + 2, w + 2), np.uint8)
    point = (42, 110)  # <----- change point here
    cv2.floodFill(closed_canny, mask, point, 255);
    mask = mask[1:h + 1, 1:w + 1]
    # mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, np.ones((3, 3), np.uint8))
    img = show_red_mask(img, mask)
    plot(img)
