import logging
import os
from matplotlib import pyplot as plt
import numpy as np
import cv2


def set_logger(log_path=None):
    """
    Set the logger to log info in terminal and file `log_path`.
    In general, it is useful to have a logger so that every output to the terminal is saved
    in a permanent file. Here we save it to `model_dir/train.log`.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Logging to a file
        # file_handler = logging.FileHandler(os.path.join(log_path, 'train.log'))
        # file_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s: %(message)s'))
        # logger.addHandler(file_handler)

        # Logging to console
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(stream_handler)


def fix_shape(img, B, H, W, method='fit'):
    """
    resize the image so that it has shape (B, H, W, 3)
    Args:
        img (Numpy array):
        B (Int): batch size of the input image
        H (Int): target height
        W (Int): target width
        method (String): type of resizing, check out the wiki of tensorboard_save_images
        for further details
    Returns:
        resized nd numpy array
    """
    # input has always shape B, H, W, 3
    res = np.zeros((B, H, W, 3))
    if method == 'fit':
        if H < img.shape[1] or W < img.shape[0]:
            raise Exception("rescale method \"fit\" can't handle images larger than the destination size")
        res[:, :img.shape[1], :img.shape[2], :] = img
    elif method == 'scale':
        for idx in range(0, B):
            res[idx] = cv2.resize(img[idx], (W, H), interpolation=cv2.INTER_AREA)
    else:
        raise Exception("please specify a valid reshape method")

    return res


def tensorboard_save_images(image_list, writer, title, iteration, shape=None, reshape_method='fit', disk_save_dir=None):
    """
    take a list of numpy array, resize them to a given shape (or the largest in the list) and print them well aligned in bulks.
    print is done on tensorboard and optionally on disk.
    Args:
        image_list (List): list of numpy array like  [img_1, img_2, ..., img_n]
        possible input shapes are:
                1 B H W
                3 B H W
                1 H W
                3 H W
        writer: tensorboard writer
        title (String): title of this plot
        iteration (Iteration for this plot):
        shape (Tuple): tuple of int with the target final shape. all the images will be resized to (H, W)
        reshape_method (String): if this is set to 'fit' each image will be placed into a numpy array with size (H, W)
        with overflow set to 0. (if the image to resize is larger than the target shape this method generates an error).
        if this is set to 'scale' each image is resized to the target image according to cv2.INTER_AREA.
        disk_save_dir (String): path where image are going to be saved or None if dump is made only on tensorboard
    Returns:
        None
    """

    # input possibili:
    # 1 B H W
    # 3 B H W
    # 1 H W
    # 3 H W

    if not isinstance(image_list, list):
        raise Exception("please provide with a list of images like [img_1, img_2, img_n]")

    if shape is not None:
        target_H, target_W = shape
    else:
        target_H, target_W  = tuple(np.array([(im.shape[-2], im.shape[-1]) for im in image_list]).max(axis=0))

    for id, image in enumerate(image_list):

        # shapes
        while len(image.shape) != 4:
            image = np.expand_dims(image, axis=0)  # creating a one dimensional batch and/or channel
        B, C, H, W = image.shape

        # creating the RGB version
        if C == 1:
            image = np.tile(image, (1, 3, 1, 1))  # B, 3, H, W
        image = np.moveaxis(image, 1, -1)  # B, H, W, 3

        # resizing
        image = fix_shape(image, B, target_H, target_W, reshape_method)

        # merging batch if present
        image = np.reshape(image, (B * target_H, target_W, 3))
        image_list[id] = image

    result = np.concatenate(
        image_list,
        axis=1
    )

    B = result.shape[0] // target_H
    step = 10 if B > 10 else B
    for i in range(B // step):
        piece = result[i * (B // 10) * target_H:(i + 1) * (B // step) * target_H]
        writer.add_image('{}/results'.format(title), np.moveaxis(piece, 2, 0), int(iteration*(B // step)+i))

        if disk_save_dir is not None:
            piece = cv2.normalize(piece, piece, 0, 255, cv2.NORM_MINMAX)
            cv2.imwrite(
                os.path.join(disk_save_dir, '{}_I{}.png'.format(title, iteration*(B // step)+i)),
                piece[:, :, ::-1]  # BGR to RGB
            )


def write_annotations(images, annotations):
    """
    create a RGB version of the input image marking with red pixels where labels are found from the input array
    Args:
        images (Numpy array): input image with shape  B, 1, H, W
        annotations (Numpy array): binary numpy array with label, same shape as images

    Returns:
        numpy array with shape B, 3, H, W
    """
    if images.shape != annotations.shape:
        raise Exception("annotations and source images have not the same shape!")
    if len(images.shape) != 4:
        images = np.expand_dims(images, axis=0)  # creating a one dimensional batch
        annotations = np.expand_dims(annotations, axis=0)

    B, C, H, W = images.shape
    # creating the RGB version
    if C == 1:
        images = np.tile(images, (1, 3, 1, 1))  # B, 3, H, W

    gt_coords = np.argwhere(annotations == 1)

    if np.max(images) > 1:
        images = images.astype(np.float32) / images.max()
    images[gt_coords[:, 0], :, gt_coords[:, 2], gt_coords[:, 3]] = (1, 0, 0)
    return images
