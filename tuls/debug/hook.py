import sys
import traceback
from contextlib import contextmanager

from tuls.debug.trace import trace, print_with_split, print_system_log


@contextmanager
def catch(enabled=True):
    try:
        yield
    except Exception as e:
        if enabled:
            print_system_log('Captured exception, extract stack and start trace.')
            print_with_split(traceback.format_exc()[:-1])
            exc_type, exc_value, exc_traceback = sys.exc_info()
            trace(exc_traceback.tb_next)
        raise e

