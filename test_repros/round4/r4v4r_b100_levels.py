from . import a
from ..pkg import c
from ...deep.mod import d
from .sub import b as bb
import os
from os import path


def via_handler():
    try:
        pass
    except Exception:
        from ..catcher import j
        return j


class K:
    def m(self, t):
        try:
            return t
        finally:
            from .fin import k
        return k


def plain():
    from ..inner import h
    return h


_G = a
if _G is not None:
    _x = c
else:
    _x = d