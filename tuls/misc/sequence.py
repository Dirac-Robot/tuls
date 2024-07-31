def renum(iterable):
    for i in reversed(range(len(iterable))):
        yield i, iterable[i]


