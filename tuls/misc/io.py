import os
from contextlib import contextmanager
from zipfile import ZipFile
from io import BytesIO


@contextmanager
def fast_write(path, mode='w'):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode) as f:
        yield f


def switch_extension(path, ext):
    return f'{os.path.splitext(os.path.basename(path))[0]}.{ext}'


def extract_zip(zip_file):
    # or: requests.get(url).content
    resp = urlopen("http://www.test.com/file.zip")
    myzip = ZipFile(BytesIO(resp.read()))
    for line in myzip.open(file).readlines():
        print(line.decode('utf-8'))
