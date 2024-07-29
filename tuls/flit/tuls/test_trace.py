import numpy as np

from tuls.debug.hook import catch


def inner_func(a, b, c):
    result = np.concatenate(a, b, c)
    return result


if __name__ == '__main__':
    x = 0.5
    y = 1.0
    z = 1.5
    with catch():
        print(inner_func(x, y, z))
