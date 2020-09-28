import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage.segmentation import inverse_gaussian_gradient, morphological_geodesic_active_contour
from conf import labels as l


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


def rescale255(img):
    """
    Rescales image value considering the maximum value in the image,
    in order to have max value 255.

    Args:
         img (np.ndarray): source image

    Returns:
        (np.ndarray): image with rescaled values
    """
    return np.array(img * (255 / img.max()), dtype=np.uint8)


def export_img(img, filename):
    """
    Exports an image

    Args:
        img (np.ndarray): source image
        filename (str): where to export
    """
    img = rescale255(img)
    print("exporting: {}".format(os.path.basename(filename)))
    cv2.imwrite(filename, img)


def active_contour_balloon(img, spline, debug=False, threshold='auto'):
    """
    Expands a spline to better fit a contour, using MorphGAC.

    Source: https://stackoverflow.com/questions/45736132/scikit-image-expanding-active-contour-snakes

    Args:
        img (np.ndarray): image
        spline (annotation.spline.Spline.Spline): spline to adapt to the image
        debug (bool): whether to show debug info/images
        threshold (str): threshold mode for MorphGAC

    Returns:
        (list of (float, float)): extracted contour
    """
    init = spline.generate_mask(img.shape)
    init[init == l.CONTOUR] = l.INSIDE
    init[init == l.BG] = 0
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


def filter_volume_Z_axis(volume, mask):
    """
    Filters part of a volume with a given mask.

    The mask must have the same dimensions of a slice on the Z axis.
    For each Z, spares only the values that corespond to the mask.

    Args:
        volume (np.ndarray): volume to filter
        mask (np.ndarray): mask image to filter with

    Returns:
        (np.ndarray): filtered volume
    """
    mask = mask.astype(np.bool_)
    gt = np.copy(volume)
    gt[:, ~mask] = 0
    return gt


def get_coords_by_label_3D(volume, label):
    """
    Selects coordinates of a volume that have a certain label,
    then converts these coordinates in three lists of z, y and x coordinates.

    Args:
        volume (np.ndarray): volume to extract labeled voxels from
        label (int): query label

    Returns:
        (list of float, list of float, list of float): z, y and x lists of coordinates
    """
    coords = np.argwhere(volume == label)
    z = [z for z, y, x in coords]
    y = [y for z, y, x in coords]
    x = [x for z, y, x in coords]
    return z, y, x


def get_coords_by_label_2D(image, label):
    """
    Selects coordinates of an image that have a certain label,
    then converts these coordinates in two lists of y and x coordinates.

    Args:
        image (np.ndarray): image to extract labeled pixels from
        label (int): query label

    Returns:
        (list of float, list of float): y and x lists of coordinates
    """
    coords = np.argwhere(image == label)
    y = [y for y, x in coords]
    x = [x for y, x in coords]
    return y, x


def get_mask_by_label(data, label):
    """
    Extracts a mask with the same shape of data (volume or image) of the points with a given label.
    Data should have labels >= 0

    Args:
         data (np.ndarray): array to filter
         label (int): query label

    Returns:
          (np.ndarray): mask
    """
    mask = np.copy(data)
    mask[mask != label] = -1
    mask[mask == label] = 0
    mask += 1
    return mask
