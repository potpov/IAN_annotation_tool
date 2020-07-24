import numpy as np


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
