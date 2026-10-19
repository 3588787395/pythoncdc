#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 synth b112a trace: instrument B112 gate + block stmts for s_plain."""
import dis
import io
import marshal
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

pyc = r'test_repros/round4/rec1_synth_b112a_asyncgen.pyc'
data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])

for const in code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name in ('s_plain', 'agen'):
        print('=' * 72)
        print('FUNC', const.co_name)
        dis.dis(const, file=sys.stdout, depth=0)

from core.cfg import region_ast_generator as RAG

_gate = RAG.RegionASTGenerator._b112_async_gen_yield_await_gate
_gbsb = RAG.RegionASTGenerator._generate_block_statements_body


def gate(self, block):
    r = _gate(self, block)
    if r is not None:
        print(f'[B112GATE] block@{block.start_offset} -> {len(r)} stmts: '
              + str([s.get('type') for s in r])[:200])
    return r


def gbsb(self, block, *a, **k):
    r = _gbsb(self, block, *a, **k)
    if any(i.opname in ('YIELD_VALUE', 'GET_AWAITABLE', 'ASYNC_GEN_WRAP') for i in block.instructions):
        print(f'[GBSB] block@{block.start_offset} ops={[i.opname for i in block.instructions]}')
        print(f'       -> {str(r)[:300]}')
    return r


RAG.RegionASTGenerator._b112_async_gen_yield_await_gate = gate
RAG.RegionASTGenerator._generate_block_statements_body = gbsb

import pycdc

src = pycdc.decompile_pyc(pyc)
open(sys.argv[1], 'w', encoding='utf-8').write(src)
print('written', sys.argv[1])
