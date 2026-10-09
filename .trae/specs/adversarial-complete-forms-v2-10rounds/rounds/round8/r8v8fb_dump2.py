#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump region tree + blocks for one code object (B98/B99 investigation helper, round8 fixB).

Usage: python r8v8fb_dump2.py <pyc> <co_name>
Writes UTF-8 to stdout; run with output redirection.
"""
import marshal
import sys
import types

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


def dump_region(r, depth=0):
    ind = '  ' * depth
    extra = []
    for attr in ('condition_block', 'merge_block', 'boolop_op', 'is_condition_context'):
        try:
            v = getattr(r, attr, None)
        except Exception:
            v = None
        if v is not None and not callable(v):
            if hasattr(v, 'start_offset'):
                extra.append('%s=@%d' % (attr, v.start_offset))
            elif isinstance(v, (str, list, bool)):
                extra.append('%s=%s' % (attr, v))
    for attr in ('then_blocks', 'op_chain', 'blocks'):
        try:
            v = getattr(r, attr, None)
        except Exception:
            v = None
        if v:
            if isinstance(v, list) and v and all(isinstance(x, tuple) for x in v):
                extra.append('%s=%s' % (attr, [(b.start_offset, o) for b, o in v]))
            else:
                try:
                    extra.append('%s=%s' % (attr, sorted(x.start_offset for x in v)))
                except Exception:
                    pass
    entry = getattr(r, 'entry', None)
    blocks = sorted(b.start_offset for b in (r.blocks or set())) if hasattr(r, 'blocks') else None
    print('%sREGION %s entry=%s blocks=%s %s' % (ind, getattr(r, 'region_type', None),
          entry and entry.start_offset, blocks, ' '.join(extra)))
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
        cfg = build_cfg(co)
        gen = RegionASTGenerator(cfg, top_level_code=None)
        an = gen.region_analyzer
        an.analyze()
        print('---- top regions (entry-filtered to non-structural) ----')
        for r in an.regions:
            dump_region(r)
        print('---- blocks ----')
        for b in cfg.get_blocks_in_order():
            ins = ' | '.join('%d:%s' % (i.offset, i.opname) for i in b.instructions)
            print('BLOCK@%d succ=%s pred=%s' % (b.start_offset,
                  sorted(s.start_offset for s in b.successors),
                  sorted(p.start_offset for p in b.predecessors)))
            print('    %s' % ins[:400])
    return 0


if __name__ == '__main__':
    sys.exit(main())
