import cv2

from annotation.tests.canal_processing import extimate_canal
from annotation.utils.image import plot


def f(img_id, point, debug=False, draw_point=False):
    original = cv2.imread(r'C:\Users\crime\Desktop\alveolar_nerve\dataset\imgs\{0:0=3d}.png'.format(img_id))
    out, _, _ = extimate_canal(original, point, debug=debug, draw_point=draw_point)
    if out is not None:
        plot(out, str(img_id))


if __name__ == '__main__':
    f(60, (56, 85), draw_point=True)
    f(100, (45, 110), draw_point=True)
    f(400, (40, 130), draw_point=True)
    f(593, (60, 64), draw_point=True)
