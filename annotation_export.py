import argparse
import os
import time
from multiprocessing import cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
from annotation.core.ArchHandler import ArchHandler


def parse_args():
    def dir_path(string):
        if os.path.isdir(string):
            return string
        else:
            raise NotADirectoryError(string)

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", dest='dir', type=dir_path, required=True, help="Directory to explore to find DICOMDIR")
    parser.add_argument("-f", dest='forced', action='store_true', required=False, default=False,
                        help="Force re-computation even if gt_volume.npy already exists")
    parser.add_argument("-w", dest='workers', type=int, required=False, default=cpu_count(),
                        help="Amount of workers for concurrent extraction")
    return parser.parse_args()


def delete_file(file_path):
    if os.path.isfile(file_path):
        os.remove(file_path)


def export_gt_volume_npy(dicomdir):
    ah = ArchHandler(dicomdir)
    ah.__init__(dicomdir)
    if ah.gt_volume.any() == True:
        ah.compute_initial_state(96, want_side_volume=False)
        ah.extract_data_from_gt(load_annotations=True)
        ah.compute_side_volume(ah.SIDE_VOLUME_SCALE, True)
    elif ah.is_there_data_to_load():
        ah.load_state()
    ah.export_gt_volume()
    ah.export_annotations_as_imgs()


if __name__ == '__main__':
    args = parse_args()
    dicomdirs = []

    print("Analyzing {}".format(args.dir))
    for root, dirs, files in os.walk(args.dir):
        if os.path.basename(root) == "annotated_dicom":
            continue
        if "DICOMDIR" in files:
            gt_volume_npy = os.path.join(root, "gt_volume.npy")
            if args.forced:
                delete_file(gt_volume_npy)
            if os.path.isfile(gt_volume_npy) and not args.forced:
                continue
            dicomdirs.append(os.path.join(root, "DICOMDIR"))

    num_dicoms = len(dicomdirs)

    t_start = time.time()

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(export_gt_volume_npy, dicomdir) for dicomdir in dicomdirs]

        kwargs = {
            'total': len(futures),
            'unit_scale': True,
            'leave': True
        }

        for f in tqdm(as_completed(futures), **kwargs):
            pass

    t_end = time.time()

    print("DICOMs: {}".format(num_dicoms))
    print("Workers: {}".format(args.workers))
    minutes = (t_end - t_start) / 60
    print("Time: {} minutes".format(minutes))
    print("Minutess per DICOM: {}".format(minutes / num_dicoms))
