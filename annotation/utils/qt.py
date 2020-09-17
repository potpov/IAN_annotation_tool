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
