#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 trace4: logging sets for generated_blocks/generated_offsets + GBS entry stacks.

用法: python _r4_trace4.py <pyc> <qualname-substr>
"""
import io
import json
import marshal
import os
import sys
import traceback
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import build_cfg
from core.cfg import region_ast_generator as RAG

WATCH_OFFSETS = {42, 50, 58}


class LogSet(set):
    def __init__(self, name):
        super().__init__()
        self._name = name

    def _describe(self, item):
        if isinstance(item, int):
            return 'off:%s' % item
        so = getattr(item, 'start_offset', None)
        return 'block@%s' % so

    def add(self, item):
        if (isinstance(item, int) and item in WATCH_OFFSETS) or \
           (not isinstance(item, int) and getattr(item, 'start_offset', None) in WATCH_OFFSETS):
            print('>>> %s.add(%s)' % (self._name, self._describe(item)))
            for line in traceback.format_stack(limit=8)[:-1]:
                print('    ' + line.strip().replace('\n', ' | '))
        super().add(item)

    def update(self, items, *a):
        for it in items:
            self.add(it)


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if name in const.co_qualname or name in const.co_name:
                out.append(const)
            find_code(const, name, out)


def main():
    pyc = sys.argv[1]
    name = sys.argv[2]
    data = open(pyc, 'rb').read()
    code = marshal.loads(data[16:])
    targets = []
    find_code(code, name, targets)
    co = targets[-1]
    print('trace code=', co.co_qualname)

    orig_body = RAG.RegionASTGenerator._generate_block_statements_body

    def body(self, block, _cjb_parent=None):
        if getattr(block, 'start_offset', None) in WATCH_OFFSETS:
            print('[GBSB-entry] block@%s in_generated_blocks=%s' % (
                block.start_offset, block in self.generated_blocks))
            for line in traceback.format_stack(limit=10)[:-1]:
                print('    ' + line.strip().replace('\n', ' | '))
        res = orig_body(self, block, _cjb_parent)
        if getattr(block, 'start_offset', None) in WATCH_OFFSETS:
            print('[GBSB-exit] block@%s -> %s' % (
                block.start_offset, json.dumps(res, default=str)[:600]))
        return res

    RAG.RegionASTGenerator._generate_block_statements_body = body

    cfg = build_cfg(co)
    gen = RAG.RegionASTGenerator(cfg, top_level_code=None)
    gen.generated_blocks = LogSet('generated_blocks')
    gen.generated_offsets = LogSet('generated_offsets')
    ast = gen.generate()
    print('DONE')
    print(json.dumps(ast, default=str)[:3000])


if __name__ == '__main__':
    main()
