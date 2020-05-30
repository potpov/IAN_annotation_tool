import cv2
import numpy as np
import pathlib
import json
import math
from tqdm import tqdm
from conf import conf
import os


def generate_mask(data):
    """
    generate a binary mask from a labelme json file
    :param data: data loaded from the json
    :return: binary image
    """

    # image info
    original_name = data['imagePath'].split('\\')[-1][:-4]
    width = data['imageWidth']
    height = data['imageHeight']

    # mask
    filename = '{}_map.jpg'.format(original_name).lstrip("0")
    mask = np.zeros((height, width), np.uint8)

    # draw all shapes from 'data' json
    for shape in data['shapes']:
        if shape['shape_type'] == 'circle':
            cx, cy = np.int32(shape['points'][0])
            px, py = np.int32(shape['points'][1])
            r = np.int32(math.sqrt((px - cx) ** 2 + (py - cy) ** 2))
            mask = cv2.circle(mask, (cx, cy), r, [255, 255, 255], cv2.FILLED)
        elif shape['shape_type'] == 'rectangle':
            tl_x, tl_y = np.int32(shape['points'][0])
            br_x, br_y = np.int32(shape['points'][1])
            mask = cv2.rectangle(mask, (tl_x, tl_y), (br_x, br_y), [255, 255, 255], cv2.FILLED)
        else:
            # generic polygon
            contour = np.array(shape['points'], np.int32)
            mask = cv2.fillPoly(mask, [contour], [255, 255, 255])

    cv2.imwrite(os.path.join(conf.SAVE_DIR, filename), mask)


def main():
    filelist = []

    for f in pathlib.Path(conf.JSON_DIR).iterdir():
        if str(f).lower().endswith('.json'):
            filelist.append(f)

    for file in tqdm(filelist):
        with open(str(file)) as data_file:
            generate_mask(json.load(data_file))


if __name__ == '__main__':
    pathlib.Path(conf.SAVE_DIR).mkdir(parents=True, exist_ok=True)
    main()