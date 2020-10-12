import os
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
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    dicomdirs = []

    dirs = [f.path for f in os.scandir(args.dir) if f.is_dir()]

    missing = dirs.copy()

    for dir in tqdm(dirs):
        for root, dirs, files in os.walk(dir):
            if "DICOMDIR" in files:
                missing.remove(dir)

    if missing:
        print("Missing DICOMDIR in:")
        for miss in missing: print(miss)
    else:
        print("Everything OK")
