import glob
import os
from typing import overload

from parse import *

from tuls.data.constants import IMAGE_EXTENSIONS


def load_all_image_paths(source):
    if not source.endswith('{ext}'):
        source = os.path.join(source, '*.{ext}')
    image_paths = []
    for ext in IMAGE_EXTENSIONS:
        image_paths.extend(glob.glob(source.format(ext=ext)))
    return image_paths


class PathFinder:
    @classmethod
    def map_by_number(cls, paths=None, path_format=None, map_fn=None):
        if paths is None:
            paths = glob.glob(path_format)
        parse_format = path_format.replace('*', '{:d}')
        numbers = [int(parse(parse_format, path)[0]) for path in paths]
        return map_fn(numbers, paths) if map_fn is not None else numbers, paths

    @classmethod
    def map_by_time(cls, path_format, map_fn):
        paths = glob.glob(path_format)
        times = [os.path.getmtime(path) for path in paths]
        return map_fn(times, paths)

