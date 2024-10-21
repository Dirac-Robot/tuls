def convert_all_layers(module, src, dst, init_kwargs_mapping, attrs_mapping, **kwargs):
    converted_module = module
    if isinstance(module, src):
        kwargs.update({
            key: getattr(module, getter) if isinstance(getter, str) else getter(module)
            for key, getter in init_kwargs_mapping.items()
        })
        converted_module = dst(**kwargs)
        for getter, dst_attr_name in attrs_mapping.items():
            setattr(
                converted_module,
                dst_attr_name,
                getattr(module, getter) if isinstance(getter, str) else getter(module)
            )
    for name, child in module.named_children():
        converted_module.add_module(
            name, convert_all_layers(child, src, dst, init_kwargs_mapping, attrs_mapping, **kwargs)
        )
    del module
    return converted_module
