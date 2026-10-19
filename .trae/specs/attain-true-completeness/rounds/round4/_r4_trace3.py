#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 trace3: patch _generate_block_statements wrapper + B31 gate + generated_offsets logging.
用法: python _r4_trace3.py <pyc> <qualname-substr>
"""
import io
import json
import marshal
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import build_cfg
from core.cfg import region_ast_generator as RAG


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

    orig = RAG.RegionASTGenerator._generate_block_statements

    def gbs(self, block, _cjb_parent=None):
        off = block.start_offset if block is not None else None
        pre = set()
        if off is not None:
            pre = {i.offset for i in block.instructions if i.offset in self.generated_offsets}
        res = orig(self, block, _cjb_parent)
        if off in (42, 50, 58, 44, 60, 62, 64, 24, 26, 66, 90, 98):
            print('[GBS] block@%s pre_gen_offsets=%s' % (off, sorted(pre)))
            print('   -> %s' % json.dumps(res, default=str)[:900])
        return res

    RAG.RegionASTGenerator._generate_block_statements = gbs
    cfg = build_cfg(co)
    gen = RAG.RegionASTGenerator(cfg, top_level_code=None)

    # wrap generated_offsets.add via a custom set-like proxy is complex; instead
    # log after each region generation using _generate_region wrapper.
    orig_gr = RAG.RegionASTGenerator._generate_region

    def gr(self, region):
        res = orig_gr(self, region)
        if type(region).__name__ in ('WithRegion', 'LoopRegion', 'IfRegion'):
            print('[REGION] %s entry@%s -> %s' % (
                type(region).__name__,
                getattr(region, 'entry', None) and region.entry.start_offset,
                json.dumps(res, default=str)[:500]))
        return res

    RAG.RegionASTGenerator._generate_region = gr
    ast = gen.generate()
    print('DONE')
    print(json.dumps(ast, default=str)[:4000])


if __name__ == '__main__':
    main()
