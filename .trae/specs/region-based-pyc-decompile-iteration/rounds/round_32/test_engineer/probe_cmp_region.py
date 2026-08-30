# -*- coding: utf-8 -*-
"""对比目标函数与 A5 变体的 LoopRegion 详细块结构。"""
import marshal
import subprocess
import sys
import os

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)
W = os.path.join(ROOT, ".trae", "specs", "region-based-pyc-decompile-iteration",
                 "rounds", "round_32", "test_engineer")

from core.cfg.region_ast_generator import RegionASTGenerator

TARGETS = {"order_response_order_update"}
_cur = {"name": None, "out": []}
_orig_generate = RegionASTGenerator.generate
_orig_ar = RegionASTGenerator._generate_region


def dump_region(region):
    rtype = type(region).__name__
    blocks = list(getattr(region, 'blocks', []) or [])
    offs = sorted(getattr(b, 'start_offset', -1) for b in blocks)
    _cur["out"].append("--- %s  blocks=%s" % (rtype, offs))
    seen = set()
    for attr in ('entry', 'cond_block', 'true_block', 'false_block',
                 'value_block', 'merge_block', 'exit_block', 'body_block',
                 'for_iter_setup', 'else_blocks'):
        b = getattr(region, attr, None)
        if b is None:
            continue
        if isinstance(b, (list, set)):
            for bb in b:
                _cur["out"].append("  [%s] off=%s" % (attr, getattr(bb, 'start_offset', '?')))
            continue
        seen.add(id(b))
        _cur["out"].append("  [%s] off=%s" % (attr, getattr(b, 'start_offset', '?')))


def patched(self):
    name = getattr(getattr(self.cfg, 'code', None), 'co_name', None)
    if name in TARGETS:
        _cur["name"] = name

        def ar(gen, region, *a, **kw):
            dump_region(region)
            return _orig_ar(gen, region, *a, **kw)

        RegionASTGenerator._generate_region = ar
        try:
            r = _orig_generate(self)
        finally:
            RegionASTGenerator._generate_region = _orig_ar
        return r
    return _orig_generate(self)


RegionASTGenerator.generate = patched


def dump_for(pyc_path, label):
    _cur["out"] = []
    import pycdc
    pycdc.decompile_pyc(pyc_path, use_cfg=True)
    print("=====", label, "=====")
    for line in _cur["out"]:
        print(line)


dump_for(r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc", "TARGET pyc")
dump_for(os.path.join(W, "variant_work", "A5_return_in_try.pyc"), "A5 variant")
