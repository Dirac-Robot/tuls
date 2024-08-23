import os
from contextlib import contextmanager


@contextmanager
def fast_write(path, mode='w'):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode) as f:
        yield f


def get_file_name(path, ext=None):
    file_name = os.path.splitext(os.path.basename(path))[0]
    if ext is not None:
        file_name = f'{file_name}.{ext}'
    return file_name

