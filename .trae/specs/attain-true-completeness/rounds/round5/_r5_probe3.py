#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump disassembly + CFG blocks + region tree for a function in a pyc.

usage: python _r5_probe3.py <pyc> <qualname-substr> [--blocks] [--ast]
"""
import io
import marshal
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if name in const.co_qualname or name in const.co_name:
                out.append(const)
            find_code(const, name, out)


def blk(b):
    if b is None:
        return None
    if isinstance(b, int):
        return '@%s' % b
    return '@%s' % getattr(b, 'start_offset', None)


def dump_region(r, indent=0):
    pad = '  ' * indent
    t = type(r).__name__
    print('%s%s entry=%s' % (pad, t, blk(getattr(r, 'entry', None))))
    for attr in ('merge_block', 'subject_block'):
        v = getattr(r, attr, None)
        if v is not None:
            print('%s  %s=%s' % (pad, attr, blk(v)))
    for attr in ('case_blocks', 'case_bodies', 'case_guards', 'case_patterns',
                 'pattern_check_blocks', 'body', 'else_body', 'then_body'):
        v = getattr(r, attr, None)
        if v is None:
            continue
        try:
            if attr == 'case_bodies':
                print('%s  %s=%s' % (pad, attr, [[blk(x) for x in body] for body in v]))
            elif attr == 'case_guards':
                print('%s  %s=%s' % (pad, attr, v))
            elif attr == 'case_patterns':
                print('%s  %s=%s' % (pad, attr, v))
            elif attr in ('case_blocks', 'pattern_check_blocks'):
                print('%s  %s=%s' % (pad, attr, [blk(x) for x in v]))
            else:
                print('%s  %s=%s' % (pad, attr, [blk(x) for x in v]))
        except Exception as e:
            print('%s  %s=<%s>' % (pad, attr, e))
    try:
        print('%s  blocks=%s' % (pad, [blk(x) for x in sorted(r.blocks, key=lambda b: b.start_offset)]))
    except Exception:
        pass
    for c in getattr(r, 'children', []) or []:
        dump_region(c, indent + 1)


def main():
    pyc = sys.argv[1]
    name = sys.argv[2]
    show_blocks = '--blocks' in sys.argv
    show_ast = '--ast' in sys.argv
    data = open(pyc, 'rb').read()
    code = marshal.loads(data[16:])
    targets = []
    find_code(code, name, targets)
    if not targets:
        print('NOT FOUND', name)
        return
    co = targets[-1]
    print('code=%s qualname=%s flags=%d' % (co.co_name, co.co_qualname, co.co_flags))
    import dis
    print('=== disassembly ===')
    for ins in dis.get_instructions(co):
        print('%5d %-30s %r' % (ins.offset, ins.opname, ins.argval))
    cfg = build_cfg(co)
    if show_blocks:
        print('=== blocks ===')
        for b in cfg.get_blocks_in_order():
            eff = [(i.opname, i.argval) for i in b.instructions
                   if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            succ = [blk(s) for s in b.successors]
            exc = [blk(s) for s in (getattr(b, 'exception_successors', None) or ())]
            print('block@%-5s succ=%s exc=%s' % (b.start_offset, succ, exc))
            print('   %s' % eff)
    gen = RegionASTGenerator(cfg, top_level_code=None)
    regions = gen.region_analyzer.analyze()
    print('=== regions (%d) ===' % len(regions))
    for r in regions:
        dump_region(r)
    if show_ast:
        print('=== ast ===')
        try:
            tree = gen.generate()
            print(tree)
        except Exception as e:
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()
