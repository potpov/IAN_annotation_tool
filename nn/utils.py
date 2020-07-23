import logging
import os
from matplotlib import pyplot as plt
import numpy as np


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


def dump_results(images, labels, predictions, args, batch_id, writer):
    """
    create a set of images with the network results compared with the original images and masks
    :param images: batch of original images
    :param labels: batch of ground truth segmentation mask
    :param predictions: batch of segmentation from the network
    :param args: args
    :param batch_id: id of the batch to use as filename
    :param  writer: tensorboard writer
    :return: pass
    """

    # converting to RGB
    images = images.cpu().numpy()
    if images.shape[1] == 1:
        images = np.tile(images, (1, 3, 1, 1))  # B, 3, H, W
    images = np.moveaxis(images, 1, -1)  # B, H, W, 3

    B, H, W, _ = images.shape

    # unrolling the batch
    images = np.reshape(images, (B * H, W, 3))
    labels = np.reshape(labels, (B * H, W))
    predictions = np.reshape(predictions, (B * H, W))

    # coordinates of the ground truth, prediction and intersect
    gt_coords = np.argwhere(labels == 1)
    net_coords = np.argwhere(predictions == 1)
    intersect_coords = np.argwhere((labels.astype(int) & predictions.astype(int)) == 1)

    # drawing
    gt = images.copy()
    gt[gt_coords[:, 0], gt_coords[:, 1]] = (1, 0, 0)
    result = images.copy()
    pred = images.copy()
    pred[net_coords[:, 0], net_coords[:, 1]] = (0, 0, 1)
    result[gt_coords[:, 0], gt_coords[:, 1]] = (1, 0, 0)
    result[net_coords[:, 0], net_coords[:, 1]] = (0, 0, 1)
    result[intersect_coords[:, 0], intersect_coords[:, 1]] = (0, 1, 0)

    final = np.concatenate(
        (
            images,
            np.zeros(shape=(B * H, 5, 3)),
            gt,
            np.zeros(shape=(B * H, 5, 3)),
            pred,
            np.zeros(shape=(B * H, 5, 3)),
            result,
        ), axis=1
    )

    writer.add_image('{}/results'.format(args.experiment_name), np.moveaxis(final, 2, 0), int(batch_id))