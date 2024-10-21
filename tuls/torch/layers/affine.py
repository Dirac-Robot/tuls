from functools import partial

import torch
from torch import nn


class Affine(nn.Module):
    def __init__(self, num_features, bias=True):
        super().__init__()
        self.num_features = num_features
        self.weight = nn.Parameter(torch.ones(num_features))
        if bias:
            self.bias = nn.Parameter(torch.zeros(num_features))
        else:
            self.bias = None

    def forward(self, x, dim=None):
        size = x.size()
        weight = self.weight
        bias = self.bias
        # guess dimension to apply
        if dim is None:
            # iterate except batch dim
            for index, d in enumerate(size[1:]):
                if d == self.num_features:
                    dim = index
                    break
            else:
                raise ValueError('There is no dimension to apply Affine module.')
        weight = weight.view(*[-1 if index == dim else 1 for index in range(len(size))])
        bias = bias.view(*[-1 if index == dim else 1 for index in range(len(size))])
        return weight*x+bias


LayerScale = partial(Affine, bias=False)
