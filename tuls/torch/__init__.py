from typing import Sequence

from torch import nn


def transfer_module_or_tensor(module_or_tensor, training=None, dtype=None, device=None):
    if training is not None and isinstance(module_or_tensor, nn.Module):
        module_or_tensor.train(training)
    if dtype is not None:
        module_or_tensor = module_or_tensor.to(dtype=dtype)
    if device is not None:
        module_or_tensor = module_or_tensor.to(device=device)
    return module_or_tensor


def transfer(modules_or_tensors, training=None, dtype=None, device=None):
    if isinstance(modules_or_tensors, Sequence):
        modules_or_tensors = []
        for module in modules_or_tensors:
            modules_or_tensors.append(transfer_module_or_tensor(module, training=training, dtype=dtype, device=device))
    else:
        for name, module in modules_or_tensors.items():
            modules_or_tensors[name] = transfer_module_or_tensor(module, training=training, dtype=dtype, device=device)
    return modules_or_tensors


def get_named_parameters(modules):
    parameters = dict()
    if isinstance(modules, Sequence):
        for index, module in enumerate(modules):
            parameters.update({f'module_{index}.{name}': parameter for name, parameter in module.named_parameters()})
    else:
        for module_name, module in modules.items():
            parameters.update({f'{module_name}.{name}': parameter for name, parameter in module.named_parameters()})
    return parameters


def get_parameters(modules):
    return list(get_named_parameters(modules).values())


def set_requires_grad(module, mode=True):
    for param in module.parameters():
        param.requires_grad_(mode)


def tensor_to_numpy(x):
    return x.clone().detach().cpu().numpy()
