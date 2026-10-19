#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 e12d instrumentation: which path emits the await for f_await_cond_pos."""
import io
import json
import marshal
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import region_ast_generator as RAG

LOG = []
_orig_recon = RAG.RegionASTGenerator._reconstruct_await_block_stmts


def _recon(self, block):
    res = _orig_recon(self, block)
    LOG.append(('_reconstruct_await_block_stmts', block.start_offset,
                json.dumps(res, default=str)[:300] if res else None))
    return res


RAG.RegionASTGenerator._reconstruct_await_block_stmts = _recon

_orig_if = RAG.RegionASTGenerator._if_extract_cond_instructions
_orig_if2 = RAG.RegionASTGenerator._if_extract_condition_from_instructions


def _if1(self, cond_block, region, boolop_merge_target=None):
    res = _orig_if(self, cond_block, region, boolop_merge_target)
    LOG.append(('_if_extract_cond_instructions', cond_block.start_offset,
                json.dumps(res, default=str)[:500]))
    return res


def _if2(self, region, cond_block, cond_instrs):
    res = _orig_if2(self, region, cond_block, cond_instrs)
    LOG.append(('_if_extract_condition_from_instructions', cond_block.start_offset,
                json.dumps(res, default=str)[:500]))
    return res


RAG.RegionASTGenerator._if_extract_cond_instructions = _if1
RAG.RegionASTGenerator._if_extract_condition_from_instructions = _if2

_orig_gbsb = RAG.RegionASTGenerator._generate_block_statements_body
_cur = {'block': None}


def _gbsb(self, block, *a, **k):
    res = _orig_gbsb(self, block, *a, **k)
    try:
        if any(i.opname == 'GET_AWAITABLE' for i in block.instructions):
            LOG.append(('_generate_block_statements_body', block.start_offset,
                        json.dumps(res, default=str)[:400]))
    except Exception:
        pass
    return res


RAG.RegionASTGenerator._generate_block_statements_body = _gbsb

import pycdc

pyc = sys.argv[1]
src = pycdc.decompile_pyc(pyc)
open(sys.argv[2], 'w', encoding='utf-8').write(src)
print('===== LOG =====')
for entry in LOG:
    print(entry[0], 'block@%s' % entry[1])
    print('   ', entry[2])
