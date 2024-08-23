from itertools import cycle
from multiprocessing import Pool


def run_with_unzipped_args(args):
    func = args[0]
    return func(*args[1:])


def iterate_with_multiprocessing(num_processes, func, *args, method='imap'):
    assert method in ('map', 'imap'), f'Unsupported method: {method}'
    with Pool(num_processes) as pool:
        if method == 'imap':
            return pool.imap(run_with_unzipped_args, zip(cycle([func]), args))
        else:  # map
            return pool.map(run_with_unzipped_args, zip(cycle([func]), args))


def apply_multiprocessing(num_processes, method='imap'):
    def decorator(func):
        def inner_func(*args):
            return iterate_with_multiprocessing(num_processes, func, *args, method=method)
        return inner_func
    return decorator
