#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 e07 dis+structure dump."""
import dis
import io
import marshal
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import build_cfg


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if name in const.co_qualname or name in const.co_name:
                out.append(const)
            find_code(const, name, out)


def print_dis(co, label):
    print('==== %s : %s ====' % (label, co.co_qualname))
    dis.dis(co)
    print()


def main():
    pyc = sys.argv[1]
    data = open(pyc, 'rb').read()
    code = marshal.loads(data[16:])
    inners = []
    find_code(code, 'e07_async_closure', inners)
    inner = [c for c in inners if c.co_name == 'inner'][0]
    lc = [c for c in inners if c.co_name == '<listcomp>'][0]
    print_dis(inner, 'inner')
    print_dis(lc, 'listcomp')

    cfg = build_cfg(inner)
    blocks = cfg.blocks
    if isinstance(blocks, dict):
        items = sorted(blocks.items(), key=lambda kv: kv[0])
    else:
        items = [(b.start_offset, b) for b in blocks]
    for off, b in items:
        instrs = [(i.offset, i.opname, getattr(i, 'argval', None)) for i in b.instructions]
        succs = [s.start_offset for s in (b.successors or [])]
        preds = [p.start_offset for p in (getattr(b, 'predecessors', None) or [])]
        print('block@%s' % off, instrs)
        print('   preds=%s succs=%s exc=%s' % (
            preds, succs,
            [s.start_offset for s in (getattr(b, 'exception_successors', None) or [])]))
    for r in cfg.regions if hasattr(cfg, 'regions') else []:
        print('region', type(r).__name__, getattr(r, 'entry', None))
    print('cfg.region_analyzer regions:')
    from core.cfg.region_analyzer import RegionAnalyzer
    try:
        ra = RegionAnalyzer(cfg)
        ra.analyze()
        for r in ra.regions:
            print('  ', type(r).__name__,
                  'entry@%s' % (getattr(r.entry, 'start_offset', None) if getattr(r, 'entry', None) else None),
                  'blocks=%s' % [getattr(b, 'start_offset', None) for b in getattr(r, 'blocks', [])])
    except Exception as e:
        print('  analyze failed:', e)


if __name__ == '__main__':
    main()
