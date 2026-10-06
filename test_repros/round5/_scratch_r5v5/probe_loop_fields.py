# -*- coding: utf-8 -*-
"""探针：打印 LoopRegion 全字段 + 每个块的后继/前驱 + 回边重检块。"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../../..'))

path = sys.argv[1]
want = sys.argv[2] if len(sys.argv) > 2 else None
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion

module = load_pyc_file_v2(path)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
actual = code_obj.to_python_code() if hasattr(code_obj, 'to_python_code') else code_obj


def off(b):
    return getattr(b, 'start_offset', None)


def dump(code, indent=''):
    if want and code.co_name != want:
        for c in code.co_consts:
            if hasattr(c, 'co_code'):
                dump(c, indent + '  ')
        return
    cfg = build_cfg(code)
    print(indent + '=== code %s varnames=%s' % (code.co_name, code.co_varnames))
    for b in cfg.blocks.values():
        ops = [i.opname + ((':' + str(i.argval)) if i.argval is not None else '') for i in b.instructions]
        succ = sorted(s.start_offset for s in (b.successors or []))
        pred = sorted(p.start_offset for p in (getattr(b, 'predecessors', None) or []))
        print(indent + '  blk@%s pred=%s succ=%s :: %s' % (off(b), pred, succ, ops))
    an = RegionAnalyzer(cfg)
    an.analyze()
    for r in getattr(an, 'regions', []):
        if isinstance(r, LoopRegion):
            print(indent + '  LOOP entry=%s header=%s cond=%s back_edge=%s is_while_true=%s' % (
                off(r.entry), off(r.header_block), off(r.condition_block),
                off(r.back_edge_block), r.is_while_true))
            print(indent + '       pre_cond=%s cond_chain=%s recheck=%s back_edge_blocks=%s' % (
                sorted(off(b) for b in (r.pre_condition_blocks or [])),
                sorted(off(b) for b in (r.condition_chain_blocks or [])),
                sorted(off(b) for b in (r.condition_recheck_blocks or set())),
                sorted(off(b) for b in (r.back_edge_blocks or set()))))
            print(indent + '       body=%s init=%s blocks=%s' % (
                sorted(off(b) for b in (r.body_blocks or [])),
                sorted(off(b) for b in (r.init_blocks or [])),
                sorted(off(b) for b in (r.blocks or []))))
    for c in code.co_consts:
        if hasattr(c, 'co_code'):
            dump(c, indent + '  ')


dump(actual)