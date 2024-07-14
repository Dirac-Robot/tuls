import traceback

import torch
import torch.distributed as dist


def is_network_constructed(**kwargs):
    _kwargs = dict(backend='nccl')
    _kwargs.update(kwargs)
    dist.init_process_group(**_kwargs)
    try:
        tensor = torch.tensor(1.).cuda()
        dist.all_reduce(tensor)
        return True
    except RuntimeError:
        print(traceback.format_exc())
        return False
