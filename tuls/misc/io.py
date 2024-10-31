import os
from contextlib import contextmanager


@contextmanager
def fast_write(path, mode='w'):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode) as f:
        yield f
