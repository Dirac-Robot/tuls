from typing import Sequence, Dict


def replace_all(string: str, mappings: Dict[str, str] = None):
    if mappings is None:
        mappings = {}
    for source, target in mappings.items():
        string = string.replace(source, target)
    return string


def remove_all(string: str, targets: Sequence[str]):
    return replace_all(string, {target: '' for target in targets})


def is_hex(string: str):
    return string.startswith('0x') and all(map(lambda c: 'A' <= c <= 'F' or '0' <= c <= '9', string[2:]))


def is_string(string: str):
    string = remove_all(string, ('e+', 'e-', 'E+', 'E-', '.'))
    return not (string.isnumeric() or string in ('True', 'False', 'None') or is_hex(string))

