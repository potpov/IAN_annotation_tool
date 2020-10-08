import os
from annotation.core.ArchHandler import ArchHandler
import argparse
from tqdm import tqdm

TOOL_DIRS = ['side_volume', 'annotated_dicom', 'masks']
TOOL_FILES = ['dump.json']


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


if __name__ == '__main__':
    args = parse_args()
    dicomdirs = []

    for root, dirs, files in os.walk(args.dir):
        if "DICOMDIR" in files:
            if args.clean:
                clean(root)
            if args.forced:
                delete_dir(os.path.join(root, "side_volume"))
            dicomdirs.append(os.path.join(root, "DICOMDIR"))

    ah = None
    for dicomdir in tqdm(dicomdirs):
        if ah is None:
            ah = ArchHandler(dicomdir)
        else:
            ah.__init__(dicomdir)
        ah.compute_initial_state(96, want_side_volume=False)
        ah.extract_data_from_gt(load_annotations=False)
        try:
            ah.compute_side_volume(ah.SIDE_VOLUME_SCALE, True)
        except:
            pass
