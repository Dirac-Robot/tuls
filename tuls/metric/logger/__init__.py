import time
from contextlib import contextmanager
import inspect


class Metric:
    def __init__(self, max_size=None):
        self.values = []
        self.max_size = max_size

    def add(self, value):
        self.values.append(value)
        if self.max_size is not None and len(self.values) > self.max_size:
            self.values.pop(0)

    def mean(self, num_values=None):
        values = self.values
        if num_values is not None:
            values = values[-num_values:]
        if values:
            return self.sum(num_values)/len(values)

    def sum(self, num_values=None):
        values = self.values
        if num_values is not None:
            values = values[-num_values:]
        return sum(values)

    def value(self):
        if self.values:
            return self.values[-1]

    def reset(self):
        self.values.clear()

    def __repr__(self):
        return f'{self.value():.3f}({self.mean():.3f})'


class Timer:
    def __init__(self, max_size=None):
        self.metric = Metric(max_size=max_size)
        self.start = None

    @contextmanager
    def time_check(self):
        self.add()
        yield
        self.add(finish=True)

    def add(self, finish=False):
        end = time.time()
        if self.metric.value():
            self.metric.add(end-self.sum()-self.start)
        elif self.start is None:
            self.start = end
        else:
            self.metric.add(end-self.start)
        if finish:
            self.finish()

    def mean(self):
        return self.metric.mean()

    def sum(self):
        return self.metric.sum()

    def value(self):
        return self.metric.value()

    def finish(self):
        self.start = None

    def reset(self):
        self.metric.reset()
        self.start = None

    def eta(self, num_iters, as_string=False):
        if self.mean():
            eta = int(self.mean()*num_iters)
            if as_string:
                days = eta//86400
                eta -= days*86400
                hours = eta//3600
                eta -= hours*3600
                minutes = eta//60
                eta -= minutes*60
                seconds = eta
                return f'{days}D {hours:02d}:{minutes:02d}:{seconds:02d}'
            else:
                return eta


@contextmanager
def capture(metric_group, *var_names):
    yield
    frame = inspect.currentframe().f_back.f_back
    local_vars = frame.f_locals
    for var_name in var_names:
        if var_name in local_vars:
            metric_group[var_name].add(local_vars[var_name])

