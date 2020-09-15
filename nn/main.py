import argparse
import os
import logging
import torch
import torch.utils.data as data
from torch.utils.tensorboard import SummaryWriter
from nn.dataloader import AlveolarDataloader
from nn.models.SegNet import SegNet
import processing

import numpy as np
from tqdm import tqdm
import nn.utils as utils
from Jaw import Jaw
from Plane import Plane
import cv2
from pathlib import Path


def predict(input_cuts, model, device, writer):

    if np.any(np.isnan(input_cuts)):
        raise Exception('some resulting values are nan!')

    alveolar_data = AlveolarDataloader(args=args, data=input_cuts)

    test_loader = data.DataLoader(
        alveolar_data,
        batch_size=args.batch_size,
        num_workers=args.data_loader_workers,
        pin_memory=True,
        drop_last=False
    )

    res = []
    with torch.no_grad():
        for i, (images) in tqdm(enumerate(test_loader), total=len(test_loader)):

            images = images.to(device)
            outputs = model(images)

            outputs = outputs.data.cpu().numpy()
            images = images.cpu().numpy()
            outputs[outputs >= 0.5] = 1
            outputs[outputs < 0.5] = 0

            annotated = utils.write_annotations(images, outputs)
            utils.tensorboard_save_images(
                [images, annotated, np.zeros((63, 1, 50, 150))],
                writer,
                title=args.experiment_name,
                iteration=i,
                disk_save_dir=os.path.join(args.experiments_dir, args.experiment_name, 'picdump'),
                reshape_method='scale'
            )
            res.append(outputs)

    res = np.squeeze(np.concatenate(res))
    return res


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('--experiment_name', default="exp1", help="name of the experiment")

arg_parser.add_argument('--experiments_dir',
                        default=r'Y:\work\logs\results',
                        help="name of the experiment")

arg_parser.add_argument('--shuffle', action='store_true', help="shuffle the dataset indices? default false")
arg_parser.add_argument('--skip_contrast', action='store_true', help="skip? default false")

arg_parser.add_argument('--checkpoint_file',
                        default=r'Y:\work\logs\checkpoints\segnet_hc_absnorm\maxillo_best.pth',
                        help="if you wanna load my model, you gotta put its .pth dir here")

arg_parser.add_argument('--tb_dir', default=r"Y:\work\logs\runs", help="path for tensorboard")

arg_parser.add_argument('--dicomdir_path', default=r'Y:\work\datasets\maxillo\anonimi\PAZIENTE_2\DICOMDIR',
                        help="the filepath of the dataset file")
arg_parser.add_argument('--slice', default=96,
                        help="slice for arch detection")

arg_parser.add_argument('--num_classes', default=1, type=int, help='num class of mask')
arg_parser.add_argument('--data_loader_workers', default=8, type=int, help='num_workers of Dataloader')
arg_parser.add_argument('--batch_size', default=64, type=int, help='input batch size')
arg_parser.add_argument('--model', default="SegNet", help='used model')
arg_parser.add_argument('--angles_num', default=10, type=int, help='number of angles to test')


args = arg_parser.parse_args()
utils.set_logger()

# create folder for results
Path(os.path.join(args.experiments_dir, args.experiment_name, 'picdump')).mkdir(parents=True, exist_ok=True)


if __name__ == '__main__':
    ###########
    # NEURAL NETWORK

    cuda = torch.cuda.is_available()
    device = torch.device('cuda' if cuda else 'cpu')
    if cuda:
        logging.info(f"This model will run on {torch.cuda.get_device_name(torch.cuda.current_device())}")
    else:
        logging.info("This model will run on CPU")

    writer = SummaryWriter(log_dir=os.path.join(args.tb_dir, args.experiment_name), purge_step=0)

    model = SegNet().to(device)
    try:
        logging.info(f"Loading checkpoint '{args.checkpoint_file}'")
        checkpoint = torch.load(args.checkpoint_file)
        model.load_state_dict(checkpoint['state_dict'])
        logging.info(f"Checkpoint loaded successfully")
    except OSError as e:
        logging.info("No checkpoint exists from '{}'. Skipping...".format(args.checkpoint_dir))
        logging.info("**First time to train**")
    model.eval()

    ############
    # DICOM PRE-PROCESSING

    jaw = Jaw(args.dicomdir_path)
    jaw_old = Jaw(args.dicomdir_path)  # saving here results with the old method

    p, start, end = processing.arch_detection(jaw.get_slice(args.slice), debug=False)
    offset = 50

    l_offset, coords, h_offset, derivative = processing.arch_lines(p, start, end, offset=offset)
    # generating orthogonal lines to the offsets curves
    side_coords = processing.generate_side_coords(h_offset, l_offset, derivative, offset=2 * offset)

    cuts = []
    plane = Plane(jaw.Z, len(side_coords[1]))

    z_axis_coeff = np.load(os.path.join(Path(__file__).parent.absolute(), 'z_axis_func_coeff.npy'))
    p = np.poly1d(z_axis_coeff)

    if args.angles_num % 2 != 0:
        raise Exception("please choose an even degree number")
    if args.angles_num < 0 or args.angles_num > 180:
        raise Exception("degrees must be withing 180, we test from -angles to +angles")

    if args.skip_contrast:
        f = lambda img: img
    else:
        f = lambda img: processing.increase_contrast(img)

    for slice_num, side_coord in enumerate(side_coords):

        plane.from_line(side_coord)  # load the plane from a line
        current_z = p(slice_num / len(side_coords))  # normalized val to the function
        # FIRST ROTATION
        plane.tilt_z(-args.angles_num)
        for i in tqdm(range(0, 1 + args.angles_num * 2), total=1 + args.angles_num * 2):
            cut = jaw.plane_slice(plane)
            cuts.append(f(cut))
            plane.tilt_z(1)

    cuts = np.stack(cuts)  # put slices and angles together
    results = predict(cuts, model, device, writer)
    result_slices = np.split(results, len(side_coords), axis=0)  # split slices from angles

    for slice_num, result_slice in enumerate(result_slices):
        # select the angle with the maximum number of predicted pixels
        # values from 0 to args.angles_num * 2
        z_angle_index = np.argmax(np.sum(result_slice.reshape(1 + args.angles_num * 2, -1) == 1, axis=1))
        # values from -args.angles_num to args.angles_num
        z_angle = z_angle_index - args.angles_num
        if z_angle == 0:
            logging.info('the best angle for slice {} is default angle'.format(slice_num))
        else:
            logging.info('the best angle for slice {} is {} degrees'.format(slice_num, z_angle))

        plane.from_line(side_coords[slice_num])
        pred = cv2.resize(result_slice[args.angles_num], (plane.Z, plane.W), interpolation=cv2.INTER_AREA)
        pred[pred > 0.5] = 1
        pred[pred <= 0.5] = 0
        jaw_old.merge_predictions(plane, pred)

        # saving result with the best X rotation (NEW METHOD)
        plane.tilt_z(z_angle)
        pred = cv2.resize(result_slice[z_angle_index], (plane.Z, plane.W), interpolation=cv2.INTER_AREA)
        pred[pred > 0.5] = 1
        pred[pred <= 0.5] = 0
        jaw.merge_predictions(plane, pred)

    logging.info('process completed. results are going to be saved in {}'.format(str(os.path.join(args.experiments_dir, args.experiment_name))))

    np.save(os.path.join(args.experiments_dir, args.experiment_name, 'tiltx.npy'), jaw.get_gt_volume())  # save volume
    np.save(os.path.join(args.experiments_dir, args.experiment_name, 'old.npy'), jaw_old.get_gt_volume())  # save volume

    # #############
    # # SECOND ROTATION
    # # starting from the previous best plane
    # plane.from_line(side_coord)
    # if angle_1 != 0:
    #     plane.tilt_z(angle_1)
    # cuts = []
    # # first cut with no tilt
    # cut = jaw.plane_slice(plane)
    # cuts.append(processing.increase_contrast(cut))
    # # explore all the possible tilts
    # for i in tqdm(range(0, 179), total=179):
    #     plane.tilt_x(1)
    #     cut = jaw.plane_slice(plane)
    #     cuts.append(processing.increase_contrast(cut))
    # cuts = np.stack(cuts)
    #
    # # predict masks for all the tilts
    # results = predict(cuts, model, device, writer)

