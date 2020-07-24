import numpy as np
from pyface.qt import QtGui


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
