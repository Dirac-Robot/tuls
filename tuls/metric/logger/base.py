import time


class Metric:
    def __init__(self):
        self.values = []

    def add(self, value):
        self.values.append(value)

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
    def __init__(self):
        self.metric = Metric()
        self.start = None

    def add(self):
        end = time.time()
        if self.metric.value():
            self.metric.add(end-self.sum()-self.start)
        elif self.start is None:
            self.start = end
        else:
            self.metric.add(end-self.start)

    def mean(self):
        return self.metric.mean()

    def sum(self):
        return self.metric.sum()

    def value(self):
        return self.metric.value()

    def reset(self):
        self.metric.reset()

    def eta(self, max_iters, as_string=False):
        if self.mean():
            eta = int(self.mean()*max_iters)
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
