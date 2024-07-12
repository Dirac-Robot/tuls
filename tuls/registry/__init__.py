import json
import os
from typing import Sequence

import yaml
from beacon import xyz
from beacon.adict import ADict, mutate_attribute


class Registry(ADict):
    def to_repr_dict(self):
        repr_dict = self.clone()
        for key, value in repr_dict.items():
            repr_dict[key] = self._to_repr(value)
        return repr_dict.to_dict()

    @classmethod
    def _to_repr(cls, value):
        if isinstance(value, Sequence):
            return [cls._to_repr(item) for item in value]
        elif isinstance(value, cls):
            return value.to_repr_dict()
        else:
            return value if isinstance(value, str) else repr(value)

    @mutate_attribute
    def json(self):
        return json.dumps(self.to_repr_dict())

    def dump(self, path, **kwargs):
        dir_path = os.path.dirname(os.path.realpath(path))
        os.makedirs(dir_path, exist_ok=True)
        ext = os.path.splitext(path)[1].lower()
        if ext in ('.yml', '.yaml'):
            with open(path, 'wb') as f:
                return yaml.dump(self.to_dict(), f, Dumper=yaml.Dumper, **kwargs)
        elif ext == '.json':
            with open(path, 'w') as f:
                return json.dump(self.to_dict(), f, **kwargs)
        elif ext == '.xyz':
            return xyz.dump(self.to_dict(), path, **kwargs)
        else:
            raise ValueError(f'{ext} is not a valid file extension.')


