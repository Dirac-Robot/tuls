import inspect
import io
import os
from contextlib import contextmanager

import numpy as np
from PIL.Image import Image
from beacon.adict import ADict
from cryptography.fernet import Fernet


def load_as_bytes(value):
    if isinstance(value, str):
        if os.path.exists(value):
            with open(value, 'rb') as f:
                value = f.read()
        else:
            value = value.encode('utf-8')
    elif isinstance(value, Image):
        image_io = io.BytesIO()
        value.save(image_io, format='PNG')
        image_io.seek(0)
        value = image_io.read()
    elif isinstance(value, np.ndarray):
        value = value.tobytes()
    return value


def auto_encrypt(value, key=None):
    key = key or Fernet.generate_key()
    if isinstance(key, str):
        key = key.encode('utf-8')
    fernet = Fernet(key)
    value = load_as_bytes(value)
    value = fernet.encrypt(value)
    return ADict(key=key, result=value)


def auto_decrypt(value, key):
    if isinstance(key, str):
        key = key.encode('utf-8')
    fernet = Fernet(key)
    value = load_as_bytes(value)
    value = fernet.decrypt(value)
    return ADict(key=key, result=value)


@contextmanager
def auto_crypt(*var_names, key=None):
    frame = inspect.currentframe().f_back.f_back
    local_vars = frame.f_locals
    key = key or Fernet.generate_key()
    if isinstance(key, str):
        key = key.encode('utf-8')
    for var_name in var_names:
        if var_name in local_vars:
            local_vars[var_name] = auto_decrypt(local_vars[var_name], key).result
    yield key
    for var_name in var_names:
        if var_name in local_vars:
            local_vars[var_name] = auto_encrypt(local_vars[var_name], key).result

