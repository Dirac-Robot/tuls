from typing import Sequence, Mapping, Union, overload


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


@overload
def split_into_batches(items, batch_size, cut_tail):
    pass


@overload
def split_into_batches(items, num_batches, cut_tail):
    pass


def split_into_batches(items, batch_size=None, num_batches=None, cut_tail=True):
    if batch_size is not None:
        batches = [items[index:index+batch_size] for index in range(0, len(items), batch_size)]
        if cut_tail and len(batches[-1]) < batch_size:
            batches.pop(-1)
    elif num_batches is not None:
        batch_size = len(items)//num_batches
        if not cut_tail:
            batch_size += 1
        batches = [items[index:index+batch_size] for index in range(0, len(items), batch_size)]
    else:
        raise ValueError('At least one of batch_size or num_batches must be specified.')
    return batches
