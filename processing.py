import numpy as np
import viewer
import cv2


def x_slice(volume, fixed_val):
    """
    create a lateral 2D projection for the
    :param volume: 3D numpy volume
    :param fixed_val: fixed coord over the X
    :return: 2D numpy image
    """
    return np.squeeze(volume[:, :, fixed_val])


def y_slice(volume, fixed_val):
    """
    create a front 2D projection for the
    :param volume:
    :param fixed_val:
    :return:
    """
    return np.squeeze(volume[:, fixed_val, :])


def spline_projection(volume, func, start, end):
    """
    create a panorex from the spline function
    :param volume: 3D VOXEL of the dental structure
    :param func: polynomial function describing the spline
    :param start: x coord where the spline starts
    :param end: x coord where the spline ends
    :return: 2D numpy image representing the panoramic image of the mouth
    """
    z_shape, y_shape, x_shape = volume.shape
    d = 1
    delta = 0.3
    coords = []
    x = start
    # we start from the range of X values on the X axis,
    # we create a new list X of x coords along the curve
    # we exploit the first order derivative to place values in X
    # so that f(X) is equally distant for each point in X
    while x < end:
        coords.append((x, func(x)))
        alfa = (func(x+delta/2) - func(x-delta/2)) / delta
        x = x + d * np.sqrt(1/(alfa**2 + 1))

    # creating lines parallel to the spline
    offset = 7
    high_offset = []
    low_offset = []
    for x, y in coords:
        alfa = (func(x + delta / 2) - func(x - delta / 2)) / delta  # first derivative
        alfa = -1 / alfa  # perpendicular coeff
        cos = np.sqrt(1/(alfa**2 + 1))
        sin = np.sqrt(alfa ** 2 / (alfa ** 2 + 1))
        if alfa > 0:
            low_offset.append((x + offset * cos, y + offset * sin))
            high_offset.append((x - offset * cos, y - offset * sin))
        else:
            low_offset.append((x - offset * cos, y + offset * sin))
            high_offset.append((x + offset * cos, y - offset * sin))

    # better re-projection using bi-linear interpolation
    panorex = np.zeros((z_shape, len(coords)), np.int)
    for idx, (x, y) in enumerate(coords):
        panorex[:, idx] = simple_interpolation(x, y, volume)

    # re-projection of the offsets curves
    panorex_up = np.zeros((z_shape, len(high_offset)), np.int)
    for idx, (x, y) in enumerate(high_offset):
        panorex_up[:, idx] = simple_interpolation(x, y, volume)

    panorex_down = np.zeros((z_shape, len(low_offset)), np.int)
    for idx, (x, y) in enumerate(low_offset):
        panorex_down[:, idx] = simple_interpolation(x, y, volume)

    viewer.plot_2D(panorex_down, cmap='bone')
    viewer.plot_2D(panorex, cmap='bone')
    viewer.plot_2D(panorex_up, cmap='bone')

    avg = np.average(np.stack([panorex_down + panorex + panorex_up]), axis=0).astype(np.uint16)
    viewer.plot_2D(avg, cmap='bone')

    # sharpening
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    avg = cv2.filter2D(avg, -1, kernel)
    viewer.plot_2D(avg, cmap='bone')

    return panorex


def get_annotations(metadata):
    """
    return a mask which maps on each pixel of the input image a ground truth value 0 or 1
    :param metadata: metadata for a given slice
    :return: mask extracted from the metadata
    """
    '''
    # alternative method that does not work that good
    overlay_data = dcm[0x6004, 0x3000].value
    rows = dcm[0x6004, 0x0010].value
    cols = dcm[0x6004, 0x0011].value

    btmp = np.frombuffer(overlay_data, dtype=np.uint8)
    btmp = np.unpackbits(btmp)
    btmp = btmp[:rows * cols]
    btmp = np.reshape(btmp, (rows, cols))
    return btmp
    '''
    return metadata.overlay_array(0x6004)


def simple_normalization(slice):
    """
    normalize data between 0 and 1
    :param slice: numpy image
    :return: numpy normilized image
    """
    return slice / slice.max()


def simple_interpolation(x_func, y_func, volume):
    """
    simple interpolation between four pixels of the image given a float set of coords
    :param x_func: float x coord
    :param y_func: float y coord on the spline
    :param volume: 3D volume of the dental image
    :return: a numpy array over the Z axis of the volume on a fixed (x,y) obtained by interpolation
    """
    x1, x2 = int(np.ceil(x_func)), int(np.floor(x_func))
    y1, y2 = int(np.ceil(y_func)), int(np.floor(y_func))
    dx, dy = x_func - x2, y_func - y2
    P1 = volume[:, y1, x1] * (1 - dx) * (1 - dy)
    P2 = volume[:, y2, x1] * dx * (1 - dy)
    P3 = volume[:, y1, x2] * dx * dy
    P4 = volume[:, y2, x2] * (1 - dx) * dy
    return np.sum(np.stack((P1, P2, P3, P4)), axis=0)


def compute_skeleton(img):
    """
    create the skeleton using morphology
    :param img: source image
    :return: image with the same input shape, b&w: 0 background, 255 skeleton elements
    """
    img = img.astype(np.uint8)
    size = img.size
    skel = np.zeros(img.shape, np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    while True:
        eroded = cv2.erode(img, kernel)
        temp = cv2.dilate(eroded, kernel)
        temp = cv2.subtract(img, temp)
        skel = np.bitwise_or(skel, temp)
        img = eroded.copy()
        zeros = size - cv2.countNonZero(img)
        if zeros == size:
            return skel


def arch_detection(slice, debug=False):
    """
    compute a polynomial spline of the dental arch from a DICOM file
    :param slice: the source image
    :return: a polinomial funtion, start and end X coords from there the dental arch can be tracked
    """
    if debug:
        viewer.plot_2D(slice)
    # initial closing
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    arch = cv2.morphologyEx(slice, cv2.MORPH_CLOSE, kernel)
    # simple threshold -> float to uint8
    ret, arch = cv2.threshold(arch, 0.5, 1, cv2.THRESH_BINARY)
    arch = arch.astype(np.uint8)
    if debug:
        viewer.plot_2D(arch)

    # hole filling
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
    arch = cv2.morphologyEx(arch, cv2.MORPH_CLOSE, kernel)
    if debug:
        viewer.plot_2D(arch)

    # major filtering with labelling
    ret, labels = cv2.connectedComponents(arch)
    for label in range(1, ret):
        if labels[labels == label].size < 10000:
            labels[labels == label] = 0
    if debug:
        viewer.plot_2D(labels)

    # compute skeleton
    skel = compute_skeleton(labels)
    if debug:
        viewer.plot_2D(skel)

    # labelling on the resulting skeleton
    cs, im = cv2.findContours(skel, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    filtered = []
    for c in cs:
        if len(c) > 40:
            filtered.append(c)

    # creating the mask of chosen pixels
    contour = np.zeros(skel.shape, np.uint8)
    cv2.drawContours(contour, filtered, -1, 255)
    if debug:
        viewer.plot_2D(contour)

    # regression polynomial function
    coords = np.argwhere(contour > 0)
    y = [y for y, x in coords]
    x = [x for y, x in coords]
    pol = np.polyfit(x, y, 12)
    p = np.poly1d(pol)

    # generating the curve for a check
    if debug:
        recon = np.zeros(skel.shape, np.uint8)  # binary image for test
        original_rgb = np.tile(slice, (3, 1, 1))  # overlay on the original image (colorful)
        original_rgb = np.moveaxis(original_rgb, 0, -1)
        for sample in range(min(x), max(x)):
            y_sample = p(sample)
            recon[int(y_sample), sample] = 255
            original_rgb[int(y_sample), sample, :] = (255, 0, 0)
        viewer.plot_2D(recon)
        viewer.plot_2D(original_rgb, cmap=None)

    return p, min(x), max(x)

