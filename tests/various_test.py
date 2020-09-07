import viewer
from Jaw import Jaw
from conf import conf
import processing
from Plane import Plane
import numpy as np
from mayavi import mlab
import imageio
from tqdm import tqdm
import cv2
import os
from dicom_loader import dicom_from_dicomdir
from pydicom.filereader import read_dicomdir
import matplotlib.pyplot as plt
import math


CUT_SLICE_NUM = 96


def snapshot(num_slice, side_coords, jaw):
    curr_cords = side_coords[num_slice]
    line3d = np.zeros_like(jaw.get_volume())
    line3d[
        CUT_SLICE_NUM,
        curr_cords[:, 1].astype(np.int),
        curr_cords[:, 0].astype(np.int)
    ] = 1

    fig = mlab.figure()
    mlab.contour3d(line3d, color=(0, 0, 0), line_width=100, figure=fig)
    mlab.contour3d(jaw.get_volume(), color=(1, 1, 1), opacity=.2, figure=fig)
    mlab.contour3d(jaw.get_gt_volume(), color=(1, 0, 0), figure=fig)
    mlab.text(
        color=(0, 0, 0),
        y=curr_cords[0][1],
        z=curr_cords[0][0],
        x=CUT_SLICE_NUM - 25,
        width=.1,
        text='slice {}'.format(str(num_slice)),
        figure=fig
    )
    # front view
    mlab.view(
        distance=800,
        elevation=270,
        focalpoint=(
            jaw.Z // 2,
            jaw.H // 2,
            jaw.W // 2
        ),
        azimuth=45,
        roll=0
    )
    fig.scene._lift()
    front_3d = mlab.screenshot(figure=fig)

    # back
    mlab.view(
        distance=800,
        elevation=270,
        focalpoint=(
            jaw.Z // 2,
            jaw.H // 2,
            jaw.W // 2
        ),
        azimuth=270,
    )
    fig.scene._lift()
    back_3d = mlab.screenshot(figure=fig)
    mlab.close(fig)
    return front_3d, back_3d


def check_line_level(dicomdir=r'C:\Users\marco\Desktop\3D_ann_dicom\DICOMDIR'):
    jaw = Jaw(dicomdir)

    section = jaw.get_slice(CUT_SLICE_NUM)
    p, start, end = processing.arch_detection(section, debug=False)

    # get the coords of the spline + 2 offset curves
    l_offset, coords, h_offset, derivative = processing.arch_lines(p, start, end)

    # generating orthogonal lines to certthe offsets curves
    side_coords = processing.generate_side_coords(h_offset, l_offset, derivative)
    plane = Plane(plane_z=jaw.Z, plane_w=len(side_coords[0]))

    results = []
    for slice_num in tqdm(range(0, len(side_coords), 27)):
        curr_cords = side_coords[slice_num]
        plane.from_line(curr_cords)
        img = jaw.plane_slice(plane)
        img = processing.grey_to_rgb(img)

        gt = jaw.plane_slice(plane, cut_gt=True)
        gt_coords = np.argwhere(gt)
        img[gt_coords[:, 0], gt_coords[:, 1]] = (1, 0, 0)

        img[CUT_SLICE_NUM, :] = (0, 0, 0)
        img = cv2.resize(img, (img.shape[1] * 2, img.shape[0] * 2), interpolation=cv2.INTER_AREA)

        front, back = snapshot(slice_num, side_coords, jaw)
        front_H, front_W, _ = front.shape
        back_H, back_W, _ = back.shape
        img_H, img_W, _ = img.shape

        max_h = max(front_H, back_H, img_H)
        result = np.zeros(shape=(max_h, front_W + back_W + img_W, 3))
        result[:front_H, :front_W] = front
        result[:back_H, front_W:front_W + back_W] = back
        result[:img_H, -img_W:] = (img * 255).astype(np.int)

        results.append(result)

    imageio.mimsave(r'C:\Users\marco\Desktop\debug\positions.mp4', results, fps=1)


def check_annotations_in_bulk(dicom_dirs_list=r'C:\Users\marco\Desktop\100 Nuovi DICOMS'):
    """
    checking if some volume is annotated from the new 100 dicom list
    Args:
        dicom_dirs_list (String): list to 100 dicom files
    Returns:

    """
    OVERLAY_ADDR = 0x6000
    good = 0
    bad = 0
    ann_names = []
    for dir in os.listdir(dicom_dirs_list):
        subdir = os.listdir(os.path.join(dicom_dirs_list, dir))
        if len(subdir) == 1:
            dicomdir = os.path.join(dicom_dirs_list, dir, subdir[0], 'DICOMDIR')
        else:
            dicomdir = os.path.join(dicom_dirs_list, dir, 'DICOMDIR')  # there's a subdir

        dicom_dir_obj = read_dicomdir(os.path.join(dicomdir))
        _, dicom_files, _ = dicom_from_dicomdir(dicom_dir_obj)
        try:
            dicom_files[0].overlay_array(OVERLAY_ADDR)
            print("ANNOTATION FOUND!!")
            good += 1
            ann_names.append(dir)
        except:
            print("no annotation in {}".format(dir))
            bad += 1

    print("process completed. {}% of volumes are annotated (a total of {}.".format(good/(good+bad), good))
    print(ann_names)


def z_level_avarage(dir=r'C:\Users\marco\Desktop\3D_ann_dicom\DICOMDIR'):
    jaw = Jaw(dir)
    section = jaw.get_slice(CUT_SLICE_NUM)
    p, start, end = processing.arch_detection(section)

    # get the coords of the spline + 2 offset curves
    l_offset, coords, h_offset, derivative = processing.arch_lines(p, start, end)

    # generating orthogonal lines to certthe offsets curves
    side_coords = processing.generate_side_coords(h_offset, l_offset, derivative)
    plane = Plane(plane_z=jaw.Z, plane_w=len(side_coords[0]))

    z_level = []
    for side_coord in side_coords:
        plane.from_line(side_coord)
        pred = jaw.plane_slice(plane, cut_gt=True)

        true_coords = np.argwhere(pred)
        xyz = plane[:, true_coords[:, 0], true_coords[:, 1]]
        z_centroid = xyz.mean(axis=1)[2]
        z_level.append(float(z_centroid) if z_centroid is not None else jaw.Z // 2)

    x = np.linspace(0, 1, len(side_coords))
    y = [jaw.Z // 2 if math.isnan(y_val) else y_val for y_val in z_level]
    pol = np.polyfit(x, y, 9)
    p = np.poly1d(pol)
    np.save('z_axis_func_coeff.npy', pol)

    # seed data
    plt.plot([i for i in range(len(side_coords))], z_level)
    plt.show()
    # resulting function
    plt.plot(np.linspace(0, 1, 1000), p(np.linspace(0, 1, 1000)))
    plt.show()


def debug_voxels():
    np.load()


if __name__ == "__main__":
    debug_voxels()
