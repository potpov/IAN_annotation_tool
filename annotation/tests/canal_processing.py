import cv2
import numpy as np
from annotation.utils.image import plot, show_red_mask


def extimate_canal(src, point, debug=False, draw_point=False):
    def check_area_perc(total, section, perc):
        max_area = total * perc
        if section < max_area:
            return True
        return False

    def check_point_inside_contour(contour, point):
        ret = cv2.pointPolygonTest(contour, point, False)
        if ret >= 0:
            return True
        return False

    img = np.array(src * 255).astype(np.uint8)
    point = tuple(map(int, point))

    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if debug:
        plot(img, "gray-scale")

    # draw point
    if draw_point:
        img_point = img.copy()
        x, y = point
        img_point[y, x] = 255
        plot(img_point, "point position")

    # denoising
    img = cv2.bitwise_not(img)
    img = cv2.bilateralFilter(img, 5, 50, 50)
    if debug:
        plot(img, "bilateral filter")

    # edges
    img = cv2.Canny(img, 20, 100)
    if debug:
        plot(img, "Canny")

    # closing
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    if debug:
        plot(img, "closing")

    # fill
    h, w = img.shape
    mask = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(img, mask, point, 255);
    mask = mask[1:h + 1, 1:w + 1]

    # contours
    drawing = np.zeros_like(mask)
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    hull = cv2.convexHull(contours[0])
    cv2.drawContours(drawing, [hull], 0, (255, 255, 255), 1, 0)
    if debug:
        plot(drawing, "convex hull")

    if not check_area_perc(h * w, cv2.contourArea(hull), 0.0047) \
            or not check_point_inside_contour(hull, point):
        return None, None, None

    out = show_red_mask(src, drawing)
    if debug:
        plot(out, "output")
    return out, hull, drawing
