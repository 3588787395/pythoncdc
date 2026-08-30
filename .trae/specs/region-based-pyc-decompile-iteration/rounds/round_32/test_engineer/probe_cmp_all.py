# -*- coding: utf-8 -*-
"""对比目标函数与全部 A/B 变体的区域树结构（不依赖函数名过滤）。"""
import os
import sys

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

from core.cfg.region_ast_generator import RegionASTGenerator

_cur = {"out": [], "depth": 0}
_orig_generate = RegionASTGenerator.generate
_orig_ar = RegionASTGenerator._generate_region


def dump_region(region, depth=0):
    rtype = type(region).__name__
    blocks = sorted(getattr(b, 'start_offset', -1) for b in (getattr(region, 'blocks', []) or []))
    extra = ""
    for attr in ('entry', 'cond_block', 'true_block', 'false_block',
                 'value_block', 'merge_block', 'exit_block', 'body_block',
                 'for_iter_setup', 'back_edge_block'):
        b = getattr(region, attr, None)
        if b is not None and not isinstance(b, (list, set)):
            extra += " %s=%s" % (attr, getattr(b, 'start_offset', '?'))
    _cur["out"].append("%s- %s blocks=%s%s" % ("  " * depth, rtype, blocks, extra))


def patched(self):
    name = getattr(getattr(self.cfg, 'code', None), 'co_name', None)

    def ar(gen, region, *a, **kw):
        dump_region(region, _cur["depth"])
        _cur["depth"] += 1
        try:
            return _orig_ar(gen, region, *a, **kw)
        finally:
            _cur["depth"] -= 1

    RegionASTGenerator._generate_region = ar
    _cur["out"].append("### FUNC %s" % name)
    try:
        return _orig_generate(self)
    finally:
        RegionASTGenerator._generate_region = _orig_ar


RegionASTGenerator.generate = patched

W = os.path.join(ROOT, ".trae", "specs", "region-based-pyc-decompile-iteration",
                 "rounds", "round_32", "test_engineer", "variant_work")

import pycdc

targets = [
    (r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc", "TARGET"),
    (os.path.join(W, "A_finally_inner_try.pyc"), "A"),
    (os.path.join(W, "A2_try_wraps_all.pyc"), "A2"),
    (os.path.join(W, "A3_static_method.pyc"), "A3"),
    (os.path.join(W, "B_finally_elifchain.pyc"), "B"),
]
for pyc, label in targets:
    _cur["out"] = []
    pycdc.decompile_pyc(pyc, use_cfg=True)
    print("=" * 30, label, "=" * 30)
    for line in _cur["out"]:
        print(line)
