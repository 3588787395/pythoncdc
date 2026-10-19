#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 synth b112a trace v2: log gates + block instr offsets."""
import io
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import region_ast_generator as RAG

_gate = RAG.RegionASTGenerator._b112_async_gen_yield_await_gate
_b31 = RAG.RegionASTGenerator._b31_await_chain_gate
_gbsb = RAG.RegionASTGenerator._generate_block_statements_body
_legacy_await = RAG.RegionASTGenerator._reconstruct_await_block_stmts


def gate(self, block):
    r = _gate(self, block)
    _cn = getattr(getattr(self.cfg, 'code', None), 'co_name', '?')
    print(f'[B112] fn={_cn} block@{block.start_offset} offs={[i.offset for i in block.instructions]} -> {r if r is None else f"{len(r)} stmts"}')
    return r


def b31(self, block):
    r = _b31(self, block)
    if r is not None:
        _cn = getattr(getattr(self.cfg, 'code', None), 'co_name', '?')
        print(f'[B31] fn={_cn} block@{block.start_offset} offs={[i.offset for i in block.instructions]} -> {len(r)} stmts')
    return r


def gbsb(self, block, *a, **k):
    r = _gbsb(self, block, *a, **k)
    _cn = getattr(getattr(self.cfg, 'code', None), 'co_name', '?')
    print(f'[GBSB-END] fn={_cn} block@{block.start_offset} offs={[i.offset for i in block.instructions]} -> {str(r)[:160]}')
    return r


def legacy(self, block, *a, **k):
    r = _legacy_await(self, block, *a, **k)
    if r:
        _cn = getattr(getattr(self.cfg, 'code', None), 'co_name', '?')
        print(f'[LEGACY-AWAIT] fn={_cn} block@{block.start_offset} offs={[i.offset for i in block.instructions]} -> {str(r)[:160]}')
    return r


RAG.RegionASTGenerator._b112_async_gen_yield_await_gate = gate
RAG.RegionASTGenerator._b31_await_chain_gate = b31
RAG.RegionASTGenerator._generate_block_statements_body = gbsb
RAG.RegionASTGenerator._reconstruct_await_block_stmts = legacy

import pycdc

src = pycdc.decompile_pyc(r'test_repros/round4/rec1_synth_b112a_asyncgen.pyc')
open(sys.argv[1], 'w', encoding='utf-8').write(src)
print('written', sys.argv[1])
