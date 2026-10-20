# -*- coding: utf-8 -*-
"""R5 x05：dump 区域树（parent/children/blocks/关键字段）for with_in_match。"""
import io
import marshal
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
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


def off(b):
    return getattr(b, 'start_offset', None)


def ridx(r):
    return '#%d' % (id(r) % 100000)


def main():
    pyc, name = sys.argv[1], sys.argv[2]
    data = open(pyc, 'rb').read()
    code = marshal.loads(data[16:])
    targets = []
    find_code(code, name, targets)
    co = targets[-1]
    cfg = build_cfg(co)
    gen = RegionASTGenerator(cfg, top_level_code=None)
    regions = gen.region_analyzer.analyze()
    by_id = {}
    for i, r in enumerate(regions):
        by_id[id(r)] = 'R%d:%s@%s' % (i, type(r).__name__, off(getattr(r, 'entry', None)))
    for i, r in enumerate(regions):
        parent = getattr(r, 'parent', None)
        pstr = by_id.get(id(parent), 'None')
        ch = []
        for c in (getattr(r, 'children', None) or []):
            ch.append(by_id.get(id(c), '?'))
        print('%s %s parent=%s children=%s' % (by_id[id(r)], ridx(r), pstr, ch))
        print('    blocks=%s' % sorted(off(b) for b in (getattr(r, 'blocks', None) or [])))
        for f in ('with_blocks', 'case_blocks', 'then_blocks', 'else_blocks', 'body_blocks'):
            v = getattr(r, f, None)
            if isinstance(v, list):
                print('    %s=%s' % (f, sorted(off(b) for b in v)))
        for f in ('condition_block', 'header_block', 'merge_block', 'subject_block'):
            v = getattr(r, f, None)
            if v is not None:
                print('    %s=%s' % (f, off(v)))


if __name__ == '__main__':
    main()
