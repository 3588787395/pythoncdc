# -*- coding: utf-8 -*-
"""Round 32: 同一进程内 hook generate() + _convert_compare_full，对照 ast_dict 与 converter 入参。
用法（Python 3.11.7）：D:/Python/python.exe probe_compare_chain.py
"""
import os
import sys
import types
import marshal

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

import core.cfg.region_ast_generator as rag
import core.cfg.ast_converter as ac

PYC = r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc"


def load_code(p):
    with open(p, "rb") as f:
        f.read(16)
        return marshal.load(f)


co = load_code(PYC)

# hook generate()
_orig_gen = rag.RegionASTGenerator.generate
gen_ret = {}


def _patched_gen(self):
    d = _orig_gen(self)

    def find56(x, path, acc):
        if isinstance(x, dict):
            t = x.get("type")
            if t == "Constant":
                v = x.get("value")
                if isinstance(v, (frozenset, tuple, set)) and "5" in str(v):
                    acc.append((path, type(v).__name__, repr(v)))
            for k, v in x.items():
                if k == "type":
                    continue
                find56(v, path + "." + k, acc)
        elif isinstance(x, list):
            for i, item in enumerate(x):
                find56(item, path + "[%d]" % i, acc)

    acc = []
    find56(d, "$", acc)
    gen_ret["hits"] = acc
    return d


rag.RegionASTGenerator.generate = _patched_gen

# hook _convert_compare_full
_orig_ccf = ac.CFGASTConverter._convert_compare_full
ccf_in = []


def _patched_ccf(self, expr_dict):
    comps = expr_dict.get("comparators", [])
    for c in comps:
        if isinstance(c, dict):
            v = c.get("value")
            if isinstance(v, (frozenset, tuple, set)) and "5" in str(v):
                ccf_in.append((type(v).__name__, repr(v)))
    return _orig_ccf(self, expr_dict)


ac.CFGASTConverter._convert_compare_full = _patched_ccf

import pycdc

src = pycdc.decompile_pyc(PYC, use_cfg=True)

print("=== generate() 返回 ast_dict 中的 5/6 容器 ===")
for path, tn, rv in gen_ret.get("hits", []):
    print("  %s -> %s %s" % (path, tn, rv))
print("=== _convert_compare_full 收到的 5/6 容器 ===")
for tn, rv in ccf_in:
    print("  %s %s" % (tn, rv))
print("=== target line ===")
for i, line in enumerate(src.splitlines()):
    if "in (5, 6)" in line or "in {5, 6}" in line:
        print("  line %d: %r" % (i, line))
