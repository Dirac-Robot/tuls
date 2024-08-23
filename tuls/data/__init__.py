from typing import Sequence, Mapping, Union


def gather_by_keys(items: Sequence[Mapping], keys: Union[str, Sequence[str]]):
    if isinstance(keys, str):
        keys = [keys]
    if any(map(lambda item: any(map(lambda key: key not in item, keys)), items)):
        raise ValueError('All items must have specified keys.')
    return dict(map(lambda key: (key, [item[key] for item in items]), keys))


def scatter_by_keys(items: Mapping[str, Sequence], keys: Union[str, Sequence[str]]):
    if isinstance(keys, str):
        keys = [keys]
    items = {key: items[key] for key in keys}
    first_item = items[keys[0]]
    if any(map(lambda item: len(item) != len(first_item), items.values())):
        raise ValueError('All items must have same length.')
    return [{key: values[i] for key, values in items.items()} for i in range(len(first_item))]


def permute_mappings(items: Union[Sequence[Mapping], Mapping[str, Sequence]]):
    if isinstance(items, Sequence):
        return gather_by_keys(items, list(items[0].keys()))
    elif isinstance(items, Mapping):
        return scatter_by_keys(items, list(items.keys()))
    else:
        raise TypeError('items should be either Sequence of Mappings or Mapping of Sequences.')
