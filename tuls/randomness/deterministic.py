import random

import numpy as np
import torch
from torch.backends import cudnn


class Deterministic:
    def __init__(self, seed=None):
        self.seed = seed
        self.torch_state = None
        self.numpy_state = None
        self.python_state = None
        self.cuda_state = None
        self.cuda_state_all = None

    def __enter__(self):
        self.apply()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.restore()

    def save_state(self):
        self.torch_state = torch.get_rng_state()
        self.numpy_state = np.random.get_state()
        self.python_state = random.getstate()
        self.cuda_state = torch.cuda.get_rng_state()
        self.cuda_state_all = torch.cuda.get_rng_state_all()

    def fix(self):
        if self.seed is not None:
            cudnn.deterministic = True
            torch.manual_seed(self.seed)
            np.random.seed(self.seed)
            random.seed(self.seed)
            torch.cuda.manual_seed(self.seed)
            torch.cuda.manual_seed_all(self.seed)

    def apply(self):
        self.save_state()
        self.fix()

    def change_seed(self, seed):
        self.seed = seed
        self.fix()

    def restore(self):
        if self.seed is not None:
            cudnn.deterministic = False
            torch.set_rng_state(self.torch_state)
            np.random.set_state(self.numpy_state)
            random.setstate(self.python_state)
            torch.cuda.set_rng_state(self.cuda_state)
            torch.cuda.set_rng_state_all(self.cuda_state_all)
