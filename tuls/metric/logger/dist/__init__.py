from tuls.metric.logger import Metric
import torch
import torch.distributed as dist


class DistMetric(Metric):
    def __init__(self, max_size=None, rank=None, world_size=None):
        super().__init__(max_size=max_size)
        self.rank = rank or dist.get_rank()
        self.world_size = world_size or dist.get_world_size()

    @torch.no_grad()
    def add(self, value):
        value = torch.tensor(value/self.world_size, requires_grad=False).to(self.rank)
        dist.all_reduce(value)
        self.values.append(value.item())



