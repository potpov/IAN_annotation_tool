import os
from annotation.core.ArchHandler import ArchHandler
import argparse
from tqdm import tqdm


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
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    dicomdirs = []
    for root, dirs, files in os.walk(args.dir):
        if "DICOMDIR" in files:
            if "side_volume" in dirs and not args.forced:
                continue
            dicomdirs.append(os.path.join(root, "DICOMDIR"))

    for dicomdir in tqdm(dicomdirs):
        ah = ArchHandler(dicomdir)
        ah.compute_initial_state(96, want_side_volume=False)
        ah.extract_data_from_gt()
        try:
            ah.compute_side_volume(ah.SIDE_VOLUME_SCALE, True)
        except:
            pass
