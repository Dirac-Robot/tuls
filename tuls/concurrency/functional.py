from itertools import cycle
from multiprocessing import Pool


def run_with_unzipped_args(args):
    func = args[0]
    return func(*args[1:])


def apply_multiprocessing(num_processes, method='imap'):
    def decorator(func):
        def inner_func(*args):
            nonlocal num_processes
            with Pool(num_processes) as pool:
                return pool.imap(run_with_unzipped_args, zip(cycle([func]), *args))
        return inner_func
    assert method in ('map', 'imap'), f'Unsupported method: {method}'
    return decorator
