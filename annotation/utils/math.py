import numpy as np


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
    try:
        if len(coords) == 0 or coords is None:
            return None, None, None
        x = [x for x, y in coords]
        y = [y for x, y in coords]
        return get_poly_approx_(x, y)
    except:
        return None, None, None


def get_poly_approx_(x, y):
    """
    Computes the polynomial approximation of a curve, defined by two lists of x and y coordinates.

    Args:
        x (list of float): x coordinates
        y (list of float): y coordinates

    Returns:
        (np.poly1d, float, float): polynomial approximation, minimum x and maximum x
    """
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
