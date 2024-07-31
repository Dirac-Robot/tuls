import importlib.util as iu
import os
import random
from contextlib import contextmanager

if numpy_exists := iu.find_spec('numpy'):
    import numpy as np
if torch_exists := iu.find_spec('torch'):
    import torch
    from torch.backends import cudnn


class Deterministic:
    def __init__(self, seed=None):
        self.seed = seed
        self.python_state = None
        self.numpy_state = None
        self.torch_state = None
        self.cuda_state = None
        self.cuda_state_all = None

    def __enter__(self):
        self.apply()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.restore()

    def save_state(self):
        self.python_state = random.getstate()
        if numpy_exists:
            self.numpy_state = np.random.get_state()
        if torch_exists:
            self.torch_state = torch.get_rng_state()
            self.cuda_state = torch.cuda.get_rng_state()
            self.cuda_state_all = torch.cuda.get_rng_state_all()

    def fix(self):
        if self.seed is not None:
            random.seed(self.seed)
            if numpy_exists:
                np.random.seed(self.seed)
            if torch_exists:
                torch.manual_seed(self.seed)
                torch.cuda.manual_seed(self.seed)
                torch.cuda.manual_seed_all(self.seed)
                cudnn.deterministic = True

    def apply(self):
        self.save_state()
        self.fix()

    def change_seed(self, seed):
        self.seed = seed
        self.fix()

    def restore(self):
        if self.seed is not None:
            random.setstate(self.python_state)
            if numpy_exists:
                np.random.set_state(self.numpy_state)
            if torch_exists:
                torch.set_rng_state(self.torch_state)
                torch.cuda.set_rng_state(self.cuda_state)
                torch.cuda.set_rng_state_all(self.cuda_state_all)
                cudnn.deterministic = False
