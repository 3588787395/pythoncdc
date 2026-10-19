#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 trace: monkey-patch statement builders to log block-level conversions.
用法: python _r4_trace.py <pyc> <qualname-substr> [offset1 offset2 ...]
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
    offs = set()
    for a in sys.argv[3:]:
        try:
            offs.add(int(a))
        except ValueError:
            pass
    data = open(pyc, 'rb').read()
    code = marshal.loads(data[16:])
    targets = []
    find_code(code, name, targets)
    co = targets[-1]
    print('trace code=', co.co_qualname)

    orig_bsi = RAG.RegionASTGenerator._build_statements_from_instructions

    def bsi(self, instrs, block=None):
        res = orig_bsi(self, instrs, block)
        off = block.start_offset if block is not None else None
        if not offs or off in offs:
            print('[BSI] block@%s instrs=%s' % (off, [(i.offset, i.opname) for i in instrs]))
            print('   -> %s' % json.dumps(res, default=str)[:1200])
        return res

    orig_gbsb = RAG.RegionASTGenerator._generate_block_statements_body

    def gbsb(self, block, _cjb_parent=None):
        res = orig_gbsb(self, block, _cjb_parent)
        off = block.start_offset if block is not None else None
        if not offs or off in offs:
            print('[GBSB] block@%s' % off)
            print('   -> %s' % json.dumps(res, default=str)[:1200])
        return res

    RAG.RegionASTGenerator._build_statements_from_instructions = bsi
    RAG.RegionASTGenerator._generate_block_statements_body = gbsb
    cfg = build_cfg(co)
    gen = RAG.RegionASTGenerator(cfg, top_level_code=None)
    ast = gen.generate()
    print('DONE ast type=%s' % type(ast))
    if ast is not None:
        print(json.dumps(ast, default=str)[:4000])


if __name__ == '__main__':
    main()
