"""m01: module docstring position and statement order at root."""
MOD_CONST = 1
import os as _os
import sys
from collections import OrderedDict as _OD

_MX = _os.name
MOD_SECOND = 'second'


def _f():
    if _MX:
        for i in range(3):
            while i:
                if i > 1:
                    break
                i -= 1
    return _MX


class _C:
    X = 2

    def get(self):
        return self.X


if MOD_CONST:
    _R = [_f() for _ in range(1)]
else:
    _R = None
MOD_AFTER = _OD
del _os
assert MOD_CONST == 1
__all__ = ['MOD_CONST', 'MOD_SECOND']
