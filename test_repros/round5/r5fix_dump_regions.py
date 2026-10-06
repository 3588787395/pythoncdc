# -*- coding: utf-8 -*-
"""探针：打印 CFG 块与识别出的区域结构（只读 core/）。"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../..'))

path = sys.argv[1]
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

module = load_pyc_file_v2(path)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
actual = code_obj.to_python_code() if hasattr(code_obj, 'to_python_code') else code_obj

def dump(code, indent=''):
    cfg = build_cfg(code)
    print(indent + '=== code %s varnames=%s' % (code.co_name, code.co_varnames))
    for b in cfg.blocks.values():
        ops = [i.opname + ((':' + str(i.argval)) if i.argval is not None else '') for i in b.instructions]
        succ = sorted(s.start_offset for s in (b.successors or []))
        pred = sorted(p.start_offset for p in (getattr(b, 'predecessors', None) or []))
        print(indent + '  blk@%s role=%s pred=%s succ=%s :: %s' % (
            b.start_offset, getattr(b, 'role', None), pred, succ, ops))
    an = RegionAnalyzer(cfg)
    an.analyze()
    if os.environ.get('DUMP_OWNER'):
        for b in cfg.blocks.values():
            own = an.block_to_region.get(b)
            print(indent + '  owner blk@%s -> %s' % (
                b.start_offset, type(own).__name__ if own is not None else None))
    print(indent + '  regions:')
    for r in getattr(an, 'regions', []):
        extra = {}
        for k in ('header_block', 'condition_block', 'merge_block'):
            v = getattr(r, k, None)
            if hasattr(v, 'start_offset'):
                extra[k] = v.start_offset
        if type(r).__name__ == 'LoopRegion' and os.environ.get('DUMP_LOOP'):
            extra['pre_cond'] = sorted(getattr(b, 'start_offset', None) for b in (getattr(r, 'pre_condition_blocks', []) or []))
            extra['cond_chain'] = sorted(getattr(b, 'start_offset', None) for b in (getattr(r, 'condition_chain_blocks', []) or []))
            extra['blocks'] = sorted(getattr(b, 'start_offset', None) for b in (getattr(r, 'blocks', []) or []))
        print(indent + '    %s entry=%s %s' % (type(r).__name__,
              getattr(r.entry, 'start_offset', None), extra))
    for c in code.co_consts:
        if hasattr(c, 'co_code'):
            dump(c, indent + '    ')

dump(actual)