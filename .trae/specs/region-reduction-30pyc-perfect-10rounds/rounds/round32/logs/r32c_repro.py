# -*- coding: utf-8 -*-
"""Round 32 R32-C repro set: statements that end in POP_TOP (a value is discarded) inside the
prefix of a block that also builds a comprehension.  Witnesses must go unmatched -> matched;
controls must stay byte-identical between the two arms (sha-level invariance only -- a control
that is already defective on the landed bytes stays defective and is not evidence of a pass).

  w1 bare call then return of a nested dict comprehension   (mirrors IQCommon/utils load_ini)
  w2 bare call then return of a single dict comprehension
  w3 bare call then a plain assignment then return comprehension
  w4 two bare calls then return of a list comprehension
  w5 bare call then a comprehension *assignment* (not a return)
  c1 assignment instead of the bare call
  c2 bare call then return of a plain value
  c3 bare call then bare attribute store
  c4 comprehension assignment with no preceding bare call
  c5 bare call then return of a call result that is not a comprehension
"""


class Conf(object):
    def read(self, path):
        return None

    def values(self):
        return []

    def flush(self):
        return None


def w1(path):
    config = Conf()
    config.read(path)
    return {s.name: {k: v for k, v in s.items()} for s in config.values()}


def w2(path):
    config = Conf()
    config.read(path)
    return {k: v for k, v in config.values()}


def w3(path):
    config = Conf()
    config.read(path)
    n = 3
    return {k: v for k, v in config.values()}


def w4(path):
    config = Conf()
    config.read(path)
    config.flush()
    return [s for s in config.values()]


def w5(path):
    config = Conf()
    config.read(path)
    rows = [s for s in config.values()]
    return rows


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
    config.flush()
    config.keep = 1
    return config


def c4(path):
    config = Conf()
    rows = [s for s in config.values()]
    return rows


def c5(path):
    config = Conf()
    config.flush()
    return config.read(path)
