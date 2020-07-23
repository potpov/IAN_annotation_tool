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
import viewer
import nn.utils as utils
from Jaw import Jaw
from Plane import Plane
import cv2


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
            outputs[outputs >= 0.5] = 1
            outputs[outputs < 0.5] = 0
            utils.dump_results(images, np.zeros_like(outputs), outputs, args, i, writer)
            res.append(outputs)

    res = np.squeeze(np.concatenate(res))
    return res


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('--experiment_name', default="exp1", help="name of the experiment")

arg_parser.add_argument('--shuffle', action='store_true', help="shuffle the dataset indices?")

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

args = arg_parser.parse_args()
utils.set_logger()


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

    p, start, end = processing.arch_detection(jaw.get_slice(args.slice), debug=False)
    offset = 50

    l_offset, coords, h_offset, derivative = processing.arch_lines(p, start, end, offset=offset)
    # generating orthogonal lines to the offsets curves
    side_coords = processing.generate_side_coords(h_offset, l_offset, derivative, offset=2 * offset)

    # TODO: we have to loop over side coords later!
    for slice_num in range(20, 120):
        side_coord = side_coords[slice_num]

        plane = Plane(jaw.Z, len(side_coord))
        plane.from_line(side_coord)  # load the plane from a line

        ###########
        # FIRST ROTATION
        cuts = []
        # first cut with no tilt
        cut = jaw.plane_slice(plane)
        cuts.append(processing.increase_contrast(cut))
        # explore all the possible tilts
        for i in tqdm(range(0, 179), total=179):
            plane.tilt_z(1)
            cut = jaw.plane_slice(plane)
            cuts.append(processing.increase_contrast(cut))
        cuts = np.stack(cuts)

        # predict masks for all the tilts
        results = predict(cuts, model, device, writer)

        # select the angle with the maximum number of predicted pixels
        angle_1 = np.argmax(np.sum(results.reshape(180, -1) == 1, axis=1))
        logging.info('ROTATION 1. the best angle for this slice is {} degrees'.format(angle_1))

        #############
        # SECOND ROTATION
        # starting from the previous best plane
        plane.from_line(side_coord)
        if angle_1 != 0:
            plane.tilt_z(angle_1)
        cuts = []
        # first cut with no tilt
        cut = jaw.plane_slice(plane)
        cuts.append(processing.increase_contrast(cut))
        # explore all the possible tilts
        for i in tqdm(range(0, 179), total=179):
            plane.tilt_x(1)
            cut = jaw.plane_slice(plane)
            cuts.append(processing.increase_contrast(cut))
        cuts = np.stack(cuts)

        # predict masks for all the tilts
        results = predict(cuts, model, device, writer)

        # select the angle with the maximum number of predicted pixels
        angle_2 = np.argmax(np.sum(results.reshape(180, -1) == 1, axis=1))
        logging.info('ROTATION 2. the best angle for this slice is {} degrees'.format(angle_2))

        # saving result for this slice
        plane.from_line(side_coord)
        if angle_1 != 0:
            plane.tilt_z(angle_1)
        if angle_2 != 0:
          plane.tilt_x(angle_2)
        pred = cv2.resize(results[angle_1], (plane.Z, plane.W), interpolation=cv2.INTER_AREA)
        pred[pred > 0] = 1
        jaw.merge_predictions(plane, pred)

    # checking the result
    viewer.annotated_volume(jaw.get_volume(), jaw.get_gt_volume())
