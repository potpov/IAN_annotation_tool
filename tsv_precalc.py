from multiprocessing import cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
from annotation.core.ArchHandler import ArchHandler
import argparse
from tqdm import tqdm
import time
import sys
import warnings

if not sys.warnoptions:
    warnings.simplefilter("ignore")

TOOL_DIRS = ['side_volume', 'annotated_dicom', 'masks']
TOOL_FILES = ['dump.json', 'history.json', 'gt_volume.npy', 'volume.npy']


def parse_args():
    def dir_path(string):
        if os.path.isdir(string):
            return string
        else:
            raise NotADirectoryError(string)

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", dest='dir', type=dir_path, required=True, help="Directory to explore to find DICOMDIR")
    parser.add_argument("-f", dest='forced', action='store_true', required=False, default=False,
                        help="Force re-computation even if side volume is already available")
    parser.add_argument("-c", dest='clean', action='store_true', required=False, default=False,
                        help="Clean directory from saves and other data")
    parser.add_argument("-w", dest='workers', type=int, required=False, default=cpu_count(),
                        help="Amount of workers for concurrent side volume computation")
    return parser.parse_args()


def delete_dir(dir_path):
    import shutil

    if os.path.isdir(dir_path):
        try:
            shutil.rmtree(dir_path)
        except OSError as e:
            print("Error: %s : %s" % (dir_path, e.strerror))


def delete_file(file_path):
    if os.path.isfile(file_path):
        os.remove(file_path)


def clean(root):
    for file in TOOL_FILES:
        delete_file(os.path.join(root, file))
    for dir in TOOL_DIRS:
        delete_dir(os.path.join(root, dir))


def extract_gt(dicomdir):
    ah = ArchHandler(dicomdir)
    ah.__init__(dicomdir)
    ah.compute_initial_state(96, want_side_volume=False)
    ah.extract_data_from_gt(load_annotations=False)
    try:
        ah.compute_side_volume(ah.SIDE_VOLUME_SCALE, True)
    except:
        pass


if __name__ == '__main__':
    args = parse_args()
    dicomdirs = []

    print("Analyzing {}".format(args.dir))
    for root, dirs, files in os.walk(args.dir):
        if "DICOMDIR" in files:
            if args.clean:
                clean(root)
            side_volume_dir = os.path.join(root, "side_volume")
            if args.forced:
                delete_dir(side_volume_dir)
            if os.path.isdir(side_volume_dir) and not args.forced:
                continue
            dicomdirs.append(os.path.join(root, "DICOMDIR"))

    num_dicoms = len(dicomdirs)

    t_start = time.time()

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(extract_gt, dicomdir) for dicomdir in dicomdirs]

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
