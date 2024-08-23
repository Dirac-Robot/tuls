import glob

from tuls.data.constants import IMAGE_EXTENSIONS


def load_all_image_paths(source):
    image_paths = []
    for ext in IMAGE_EXTENSIONS:
        image_paths.extend(glob.glob(source.format(ext=ext)))
    return image_paths

