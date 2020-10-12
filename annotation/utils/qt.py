import numpy as np
from pyface.qt import QtGui
from annotation.utils.ContrastStretching import ContrastStretching


def numpy2pixmap(data):
    """
    Converts a 2D/3D numpy array to a QPixmap

    Args:
        data (np.ndarray): 2D/3D image

    Returns:
        (pyface.qt.QtGui.QPixmap): pixmap of the image
    """
    img_ = np.clip(data, 0, 1)
    cs = ContrastStretching()
    img_ = cs.stretch(img_)
    img_ = np.clip(img_ * 255, 0, 255)

    if len(img_.shape) != 3:
        img_ = np.stack((img_,) * 3, axis=-1)

    h, w, c = img_.shape
    step = w * c
    # must pass a copy of the image
    img_ = img_.astype(np.uint8)
    qimage = QtGui.QImage(img_.copy(), w, h, step, QtGui.QImage.Format_RGB888)
    pixmap = QtGui.QPixmap(qimage)
    return pixmap
