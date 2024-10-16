def clamp(x, lower=None, upper=None):
    if lower is not None and x < lower:
        return lower
    if upper is not None and x > upper:
        return upper
    return x
