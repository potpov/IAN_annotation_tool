import os
import cv2
import numpy as np
from pyface.qt import QtGui
import matplotlib.pyplot as plt
from skimage.segmentation import inverse_gaussian_gradient, morphological_geodesic_active_contour


def numpy2pixmap(data):
    """
    Converts a 2D/3D numpy array to a QPixmap

    Args:
        data (np.ndarray): 2D/3D image

    Returns:
        (pyface.qt.QtGui.QPixmap): pixmap of the image
    """
    if np.max(data) <= 1.01:  # sometimes we have max(data) == 1.00001
        img_ = (data * 255).astype(np.uint8)
    else:
        img_ = data.astype(np.uint8)
    if len(img_.shape) != 3:
        img_ = np.stack((img_,) * 3, axis=-1)
    h, w, c = img_.shape
    step = img_.nbytes / h
    # must pass a copy of the image
    qimage = QtGui.QImage(img_.copy(), w, h, step, QtGui.QImage.Format_RGB888)
    pixmap = QtGui.QPixmap(qimage)
    return pixmap


def clip_range(val, minimum, maximum):
    """
    Clips a value into a given range (saturation)

    Args:
        val (float): value to clip
        minimum (float): minimum value possible
        maximum (float): maximum value possible

    Returns:
        (float): clipped value
    """
    return max(minimum, min(val, maximum))


def fix_overflow(img, coords):
    """
    For each point in the list, clips their coordinates into the minimum and maximum values possibile inside an image.

    Args:
        img (np.ndarray): image
        coords (list of (float, float)): list of points

    Returns:
        (list of (float, float)): list of points
    """
    for idx, coord in enumerate(coords):
        coord_ = (clip_range(coord[0], 0.0, img.shape[1] - 1),
                  clip_range(coord[1], 0.0, img.shape[0] - 1))
        coords[idx] = coord_
    return coords


def get_poly_approx(coords):
    """
    Computes the polynomial approximation of a curve.

    Args:
         coords (list of (float, float)): list of points

    Returns:
        (np.poly1d, float, float): polynomial approximation, minimum x and maximum x
    """
    if len(coords) == 0 or coords is None:
        return None, None, None
    x = [x for x, y in coords]
    y = [y for x, y in coords]
    pol = np.polyfit(x, y, 12)
    p = np.poly1d(pol)
    return p, min(x), max(x)


def apply_offset_to_point(point, offset, p):
    """
    Computes the offsetted position of a point.

    It uses the polynomial approximation of the curve.

    Args:
        point ((float,float)): xy coordinates of the point
        offset (int): how much to displace the point from the original position
        p (np.poly1d): polynomial approximation of the curve

    Returns:
        (float, float): xy coordinates of the offsetted point
    """
    x, y = point
    delta = 0.3
    alpha = (p(x + delta / 2) - p(x - delta / 2)) / delta  # first derivative
    alpha = -1 / alpha  # perpendicular coeff
    cos = np.sqrt(1 / (alpha ** 2 + 1))
    sin = np.sqrt(alpha ** 2 / (alpha ** 2 + 1))
    if alpha > 0:
        return (x + offset * cos, y + offset * sin)
    else:
        return (x - offset * cos, y + offset * sin)


def apply_offset_to_arch(coords, offset, p):
    """
    Computes the offsetted position of and arch.

    It uses the polynomial approximation of the curve.

    Args:
         coords (list of (float, float)): list of points
         offset (int): how much to displace the arch from the original position
         p (np.poly1d): polynomial approximation of the curve
    """
    new_arch = []
    for point in coords:
        new_arch.append(apply_offset_to_point(point, offset, p))
    return new_arch


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
    plt.imshow(img, cmap='gray')
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


def get_square_around_point(center, im_shape, l=20):
    """
    Generates two points that define a square with the point "center" as its center.

    Args:
        center ((float, float)): center point
        im_shape ((int, int)): shape of the image, used to not overflow
        l (int): length of the side of the square

    Returns:
        ((int, int), (int, int)): top-left and bottom-right points
    """
    center = tuple(map(int, center))
    x, y = center
    h, w = im_shape
    l2 = l // 2
    P1 = (clip_range(x - l2, 0, w - 1), clip_range(y - l2, 0, h - 1))
    P2 = (clip_range(x + l2, 0, w - 1), clip_range(y + l2, 0, h - 1))
    return P1, P2


def export_img(img, filename):
    img = cv2.convertScaleAbs(img, alpha=(255.0))
    print("exporting: {}".format(os.path.basename(filename)))
    cv2.imwrite(filename, img)


def active_contour_balloon(img, spline, debug=False, threshold='auto'):
    # SRC https://stackoverflow.com/questions/45736132/scikit-image-expanding-active-contour-snakes
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
    morph_GAC = cv2.cvtColor(morph_GAC, cv2.COLOR_BGR2GRAY)
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
