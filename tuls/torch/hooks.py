import inspect

from beacon.adict import ADict


class Hook:
    def __init__(self):
        self.registry = ADict(default=ADict())

    def _module_pre_hook(self, name, inputs, pre_action=None):
        if pre_action is not None:
            return pre_action(inputs)
        self.registry[name]['pre_inputs'] = inputs

    def _module_post_hook(self, name, inputs, outputs, post_action=None):
        self.registry[name]['inputs'] = inputs
        self.registry[name]['outputs'] = outputs
        if post_action is not None:
            return post_action(outputs)

    def capture_module(self, name, module, pre_action=None, post_action=None):
        if pre_action is not None:
            module.register_forward_pre_hook(
                lambda _, inputs: self._module_pre_hook(name, inputs, pre_action)
            )
        module.register_forward_hook(
            lambda _, inputs, outputs: self._module_post_hook(name, inputs, outputs, post_action)
        )

    def capture_func(self, name, pre_action=None, post_action=None):
        def decorator(func):
            def wrapper(*args, **kwargs):
                if pre_action:
                    args, kwargs = pre_action(*args, **kwargs)
                sig = inspect.signature(func)
                bound_args = sig.bind_partial(*args, **kwargs)
                bound_args.apply_defaults()
                inputs = [bound_args.arguments[param.name] for param in sig.parameters.values()]
                outputs = func(*inputs)
                if post_action:
                    outputs = post_action(outputs)
                self.registry[name]['inputs'] = inputs
                self.registry[name]['outputs'] = outputs
                return outputs
            return wrapper
        return decorator
