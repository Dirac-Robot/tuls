import random


def renum(iterable):
    for i in reversed(range(len(iterable))):
        yield i, iterable[i]


def sample_by_ratio(items, ratio, sort=False):
    num_samples = int(len(items)*ratio)
    sample_indices = random.sample(list(range(len(items))), num_samples)
    if sort:
        sample_indices.sort()
    return [items[index] for index in sample_indices]


def sample_by_random_sampling_range(items, sampling_range, sort=False):
    lb, ub = min(sampling_range), max(sampling_range)
    ratio = random.random()*(ub-lb)+lb
    return sample_by_ratio(items, ratio, sort=sort)
