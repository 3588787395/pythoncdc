"""n10_02: 负对照 — 最简 from-import / as 别名（必须 MATCH）"""
from os import path
from collections import OrderedDict as OD


def simple_fromimport(p):
    d = OD()
    if p is not None:
        d["k"] = path.basename(p)
    return d
