#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 trace2: patch B31 gate / await chain collection.
用法: python _r4_trace2.py <pyc> <qualname-substr>
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

    orig_collect = RAG.RegionASTGenerator._collect_await_protocol_chain

    def collect(self, block):
        res = orig_collect(self, block)
        off = block.start_offset if block is not None else None
        if res is not None:
            members, owner = res
            print('[COLLECT] block@%s -> members=%s owner@%s' % (
                off, [m.start_offset for m in members],
                owner.start_offset if owner is not None else None))
        return res

    orig_gate = RAG.RegionASTGenerator._b31_await_chain_gate

    def gate(self, block):
        res = orig_gate(self, block)
        off = block.start_offset if block is not None else None
        if res is not None:
            print('[GATE] block@%s -> %s' % (off, json.dumps(res, default=str)[:800]))
        return res

    RAG.RegionASTGenerator._collect_await_protocol_chain = collect
    RAG.RegionASTGenerator._b31_await_chain_gate = gate
    cfg = build_cfg(co)
    gen = RAG.RegionASTGenerator(cfg, top_level_code=None)
    ast = gen.generate()
    print('DONE')
    print(json.dumps(ast, default=str)[:4000])


if __name__ == '__main__':
    main()
