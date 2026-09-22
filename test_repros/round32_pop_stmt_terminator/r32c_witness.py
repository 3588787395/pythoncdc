# -*- coding: utf-8 -*-
"""Round 32 line C synthetic witnesses: a bare expression statement (call whose result is
popped) immediately before a `return` whose value is a comprehension, in straight-line code.

  r32c_w1  target shape: bare call, then return dict-comprehension (outer comprehension whose
           element expression is itself a dict comprehension) -- mirrors load_ini.
  r32c_w2  bare call, then return dict-comprehension (single level).
  r32c_c1  CONTROL: assignment instead of the bare call.
  r32c_c2  CONTROL: bare call, then return of a plain (non-comprehension) expression.
  r32c_c3  CONTROL: bare call, then a plain assignment, then return comprehension.

compiled by compile32.py with an explicit cfile; nothing here depends on the corpus.
"""


class Conf(object):
    def read(self, path):
        return None

    def values(self):
        return []


def w1(path):
    config = Conf()
    config.read(path)
    return {s.name: {k: v for k, v in s.items()} for s in config.values()}


def w2(path):
    config = Conf()
    config.read(path)
    return {k: v for k, v in config.values()}


def c1(path):
    config = Conf()
    got = config.read(path)
    return {s.name: {k: v for k, v in s.items()} for s in config.values()}


def c2(path):
    config = Conf()
    config.read(path)
    return config


def c3(path):
    config = Conf()
    config.read(path)
    n = 3
    return {k: v for k, v in config.values()}
