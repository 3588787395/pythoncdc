#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R3 区域级 trace：dump 指定函数全部区域（类型/entry/blocks/关键字段）。
用法: python _r3_regions.py <pyc> <qualname> [--blocks]
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
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


def blk(b):
    return '@%s' % (b.start_offset if b is not None else None)


def main():
    pyc = sys.argv[1]
    name = sys.argv[2]
    show_blocks = '--blocks' in sys.argv
    data = open(pyc, 'rb').read()
    code = marshal.loads(data[16:])
    targets = []
    find_code(code, name, targets)
    co = targets[-1]
    cfg = build_cfg(co)
    gen = RegionASTGenerator(cfg, top_level_code=None)
    regions = gen.region_analyzer.analyze()
    print('total regions:', len(regions))
    for r in regions:
        t = type(r).__name__
        entry = getattr(r, 'entry', None)
        fields = []
        for attr in ('merge_block', 'condition_block', 'header', 'true_value_block', 'false_value_block',
                     'merge_context', 'value_target', 'finally_block', 'else_block', 'handler_entry'):
            v = getattr(r, attr, None)
            if v is not None and v is not entry:
                fields.append('%s=%s' % (attr, blk(v)))
        print('%-20s entry=%s %s' % (t, blk(entry), ' '.join(fields)))
        if show_blocks:
            try:
                print('    blocks=%s' % sorted(b.start_offset for b in r.blocks))
            except Exception:
                pass
    print('--- region block offsets (all blocks) ---')
    for b in getattr(cfg, 'blocks', []):
        last = b.get_last_instruction()
        print('  block@%-4s last=%s%s' % (b.start_offset, last and last.opname,
                                          (' arg=%r' % (last.argval,)) if last and last.argval is not None else ''))


if __name__ == '__main__':
    main()
