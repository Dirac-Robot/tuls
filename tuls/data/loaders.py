import glob
import os
from pathlib import Path

from parse import *

from tuls.data.constants import IMAGE_EXTENSIONS
from tuls.misc.sequence import ensure_sequence


def load_all_image_paths(source):
    if not source.endswith('{ext}'):
        source = os.path.join(source, '*.{ext}')
    image_paths = []
    for ext in IMAGE_EXTENSIONS:
        image_paths.extend(glob.glob(source.format(ext=ext)))
    return image_paths


class PathFinder:
    @classmethod
    def get_file_name(cls, path, ext=None):
        file_name = os.path.splitext(os.path.basename(path))[0]
        if ext is not None:
            file_name = f'{file_name}.{ext}'
        return file_name

    @classmethod
    def split(cls, path):
        return path.split(os.path.sep)

    @classmethod
    def join(cls, paths_1, paths_2):
        paths_1 = [Path(path) for path in ensure_sequence(paths_1)]
        paths_2 = [Path(path) for path in ensure_sequence(paths_2)]
        if len(paths_1) == 1:
            paths_1 = paths_1*len(paths_2)
        if len(paths_2) == 1:
            paths_2 = paths_2*len(paths_1)
        if len(paths_1) != len(paths_2):
            raise ValueError('The length of paths_1 and paths_2 must be 1 or same.')
        return [str(path_1/path_2) for path_1, path_2 in zip(paths_1, paths_2)]

    @classmethod
    def map_by_number(cls, paths=None, path_format=None, map_fn=None):
        if paths is None:
            paths = glob.glob(path_format)
        parse_format = path_format.replace('*', '{:d}')
        numbers = [int(parse(parse_format, path)[0]) for path in paths]
        return map_fn(numbers, paths) if map_fn is not None else numbers, paths

    @classmethod
    def map_by_time(cls, path_format, map_fn=None):
        paths = glob.glob(path_format)
        times = [os.path.getmtime(path) for path in paths]
        return map_fn(times, paths) if map_fn is not None else times, paths
