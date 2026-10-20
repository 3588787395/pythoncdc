#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 区域级 trace：dump 指定函数全部区域（类型/entry/blocks/关键字段）。
用法: python _r4_regions.py <pyc> <qualname-substr> [--blocks] [--all]
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
    print('code=%s qualname=%s flags=%d' % (co.co_name, co.co_qualname, co.co_flags))
    cfg = build_cfg(co)
    gen = RegionASTGenerator(cfg, top_level_code=None)
    regions = gen.region_analyzer.analyze()
    print('total regions:', len(regions))
    for r in regions:
        t = type(r).__name__
        entry = getattr(r, 'entry', None)
        fields = []
        for attr in ('merge_block', 'condition_block', 'header', 'true_value_block', 'false_value_block',
                     'merge_context', 'value_target', 'finally_block', 'else_block', 'handler_entry',
                     'try_start', 'try_end', 'handler_start'):
            v = getattr(r, attr, None)
            if v is not None and v is not entry:
                fields.append('%s=%s' % (attr, blk(v)))
        print('%-24s entry=%s %s' % (t, blk(entry), ' '.join(fields)))
        if show_blocks:
            try:
                print('    blocks=%s' % sorted(b.start_offset for b in r.blocks))
            except Exception:
                pass
    print('--- block offsets ---')
    for b in getattr(cfg, 'blocks', []):
        last = b.get_last_instruction()
        first = b.instructions[0] if b.instructions else None
        print('  block@%-4s first=%-22s last=%s%s' % (
            b.start_offset, first and first.opname, last and last.opname,
            (' arg=%r' % (last.argval,)) if last and last.argval is not None else ''))


if __name__ == '__main__':
    main()
