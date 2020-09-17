import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage.segmentation import inverse_gaussian_gradient, morphological_geodesic_active_contour


def draw_blue_vertical_line(img, pos):
    """
    Draws a blue vertical line in position pos in a 2D image img.

    Args:
         img (np.ndarray): 2D image
         pos (int): position

    Returns:
        (np.ndarray): 3D colored image with vertical line
    """
    img_rgb = np.tile(img, (3, 1, 1))
    img_rgb = np.moveaxis(img_rgb, 0, -1)
    rg = np.zeros((img.shape[0]))
    b = np.ones((img.shape[0]))
    blue_line = np.stack([rg, rg, b])
    blue_line = np.moveaxis(blue_line, 0, -1)
    img_rgb[:, pos, :] = blue_line
    return img_rgb


def enhance_contrast(img):
    """
    Enhances contrast of an image using CLAHE.

    Args:
        img (np.ndarray): image

    Returns:
        (np.ndarray): contrast enhanced image
    """
    # CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=3., tileGridSize=(8, 8))

    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)  # convert from BGR to LAB color space
    l, a, b = cv2.split(lab)  # split on 3 different channels

    l2 = clahe.apply(l)  # apply CLAHE to the L-channel

    lab = cv2.merge((l2, a, b))  # merge channels
    img2 = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)  # convert from LAB to BGR

    return img2


def sharpen(im):
    """
    Applies sharpening to and image.

    Args:
        im (np.ndarray): image

    Returns:
        (np.ndarray): sharpened image
    """
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    im = cv2.filter2D(im, -1, kernel)
    return im


def plot(img, title="plot"):
    """
    Plots an image.

    Args:
        img (np.ndarray): image
        title (str): title
    """
    plt.title(title)
    plt.imshow(img, cmap='gray', interpolation='none')
    plt.show()


def show_red_mask(img, mask):
    """
    Shows a mask onto an image with red pixels.

    Args:
        img (np.ndarray): image
        mask (np.ndarray): mask

    Returns:
        (np.ndarray): image + red mask
    """
    img_ = img
    mask_ = np.bool_(mask)
    red = img_[:, :, 0]
    green = img_[:, :, 1]
    blue = img_[:, :, 2]
    red[mask_] = 255
    green[mask_] = 0
    blue[mask_] = 0
    return img_


def export_img(img, filename):
    img = cv2.convertScaleAbs(img, alpha=(255.0))
    print("exporting: {}".format(os.path.basename(filename)))
    cv2.imwrite(filename, img)


def active_contour_balloon(img, spline, debug=False, threshold='auto'):
    # source: https://stackoverflow.com/questions/45736132/scikit-image-expanding-active-contour-snakes
    init = spline.generate_mask(img.shape)
    init.clip(max=1)
    debug and plot(init, "init")
    prep_img = inverse_gaussian_gradient(np.array(img))
    debug and plot(prep_img, "inverse_gaussian_gradient")
    morph_GAC = morphological_geodesic_active_contour(
        prep_img, 5, init, smoothing=1,
        balloon=1, threshold=threshold,
        # iter_callback=lambda x: plot(x * 255)
    )
    morph_GAC = np.array(morph_GAC * 255).astype(np.uint8)
    if not morph_GAC.any():
        return None
    morph_GAC[morph_GAC > 0] = 255
    debug and plot(morph_GAC, "morphGAC")
    try:
        contours, _ = cv2.findContours(morph_GAC, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    except:
        return None
    contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)
    contour = np.squeeze(contours[0])

    return contour
