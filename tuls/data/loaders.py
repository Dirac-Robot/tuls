import glob
import os

from tuls.data.constants import IMAGE_EXTENSIONS


def load_all_image_paths(source):
    if not source.endswith('{ext}'):
        source = os.path.join(source, '*.{ext}')
    image_paths = []
    for ext in IMAGE_EXTENSIONS:
        image_paths.extend(glob.glob(source.format(ext=ext)))
    return image_paths

