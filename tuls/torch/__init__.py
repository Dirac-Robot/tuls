import torch


def transfer_modules(module_dict, training=None, dtype=None, device=None):
    for name, module in module_dict.items():
        if training is not None:
            module.train(training)
        if dtype is None:
            module_dict[name] = module.to(device=device)
        elif device is None:
            module_dict[name] = module.to(dtype=dtype)
        else:
            module_dict[name] = module.to(dtype=dtype, device=device)
    return module_dict


def transfer_tensors(tensor_dict, dtype=None, device=None):
    for name, tensor in tensor_dict.items():
        if isinstance(tensor, torch.Tensor):
            if dtype is None:
                tensor_dict[name] = tensor.to(device=device)
            elif device is None:
                tensor_dict[name] = tensor.to(dtype=dtype)
            else:
                tensor_dict[name] = tensor.to(dtype=dtype, device=device)
    return tensor_dict
