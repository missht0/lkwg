import numpy as np

from ..interception_controller import get_controller


def _update_image_size(ctrl):
    if ctrl.cached_image is not None:
        bgr = np.asarray(ctrl.cached_image, dtype=np.uint8)
        h, w = bgr.shape[:2]
        get_controller().update_image_size(w, h)
