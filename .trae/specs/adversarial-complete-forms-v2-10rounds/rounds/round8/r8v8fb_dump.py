#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump region tree + blocks for one code object of a pyc (B104 investigation helper).

Usage: python r8v8fb_dump.py <pyc> <co_name> [--blocks] [--regions]
"""
import sys
import os
import marshal
import types
import dis

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator


def find_code(code, name):
    found = []
    def walk(c):
        for const in c.co_consts:
            if isinstance(const, types.CodeType):
                if const.co_name == name:
                    found.append(const)
                walk(const)
    walk(code)
    return found


def dump_block(b, indent):
    ins = ' | '.join('%d:%s' % (i.offset, i.opname if i.opname[-1].isalpha() or not i.opname[-1].isdigit() else i.opname) for i in b.instructions)
    print('%sBLOCK@%d (end=%d) succ=%s pred=%s' % (
        indent, b.start_offset, b.end_offset,
        sorted(s.start_offset for s in (b.successors or set())),
        sorted(p.start_offset for p in (b.predecessors or set()))))
    print('%s   %s' % (indent, ins))


def dump_region(r, depth=0):
    ind = '  ' * depth
    rt = getattr(r, 'region_type', None)
    extra = []
    for attr in ('condition_block', 'header_block', 'merge_block', 'back_edge_block',
                 'true_value_block', 'false_value_block', 'value_target', 'merge_context'):
        v = getattr(r, attr, None)
        if v is not None and not callable(v):
            if hasattr(v, 'start_offset'):
                extra.append('%s=@%d' % (attr, v.start_offset))
            elif isinstance(v, str):
                extra.append('%s=%s' % (attr, v))
    for attr in ('chained_compare_ops', 'boolop_op', 'is_negated_chained_compare'):
        v = getattr(r, attr, None)
        if v:
            extra.append('%s=%s' % (attr, v))
    for attr in ('then_blocks', 'else_blocks', 'body_blocks', 'chained_compare_blocks',
                 'condition_chain_blocks', 'finally_blocks', 'handler_blocks'):
        v = getattr(r, attr, None)
        if v:
            if isinstance(v, dict):
                keys = sorted(k.start_offset for k in v) if all(hasattr(k, 'start_offset') for k in v) else list(v)
                extra.append('%s=%s' % (attr, keys))
            else:
                try:
                    extra.append('%s=%s' % (attr, sorted(x.start_offset for x in v)))
                except Exception:
                    pass
    print('%sREGION %s entry=@%d blocks=%s %s' % (
        ind, rt, getattr(r, 'entry', None) and r.entry.start_offset,
        sorted(b.start_offset for b in (r.blocks or set())) if hasattr(r, 'blocks') else None,
        ' '.join(extra)))
    for c in (r.children or []):
        dump_region(c, depth + 1)


def main():
    pyc = sys.argv[1]
    name = sys.argv[2]
    data = open(pyc, 'rb').read()
    code = marshal.loads(data[16:])
    targets = find_code(code, name)
    if not targets:
        print('code object not found: %s' % name)
        return 1
    for co in targets:
        print('==== %s (%s) ====' % (co.co_name, co.co_qualname))
        print('---- dis ----')
        dis.dis(co)
        cfg = build_cfg(co)
        gen = RegionASTGenerator(cfg, top_level_code=None)
        analyzer = getattr(gen, 'region_analyzer', None)
        print('---- blocks ----')
        for b in cfg.get_blocks_in_order():
            dump_block(b, '')
        if '--regions' in sys.argv and analyzer is not None:
            print('---- top regions ----')
            for r in getattr(analyzer, 'regions', []):
                dump_region(r, 0)
    return 0


if __name__ == '__main__':
    sys.exit(main())
