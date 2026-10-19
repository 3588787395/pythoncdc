#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 B47 prototype: ternary arm value via await chain stream merge (monkeypatch)."""
import io
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import region_ast_generator as RAG
from core.cfg.comprehension_generator import is_async_poll_protocol_block

_CALL_OPS = ('CALL', 'CALL_FUNCTION', 'CALL_METHOD', 'CALL_FUNCTION_KW', 'CALL_FUNCTION_EX')
_TAIL_OPS = ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT', 'RETURN_VALUE', 'RETURN_CONST')


def _await_arm_value_expr(self, block):
    chain = self._collect_await_protocol_chain(block)
    if chain is None:
        return None
    members, owner = chain
    if any(i.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH')
           for m in members for i in m.instructions):
        return None
    _head = members[0]
    _hops = [i.opname for i in _head.instructions]
    if ('SWAP' in _hops and 'CALL' in _hops and 'GET_AWAITABLE' in _hops
            and sum(1 for i in _head.instructions
                    if i.opname == 'LOAD_CONST' and i.argval is None) >= 3):
        return None
    if not self._b31_continuation_owner(owner):
        return None
    merged = []
    prev_awaitable = False
    prev_call = False
    inline_pending = False
    inline_awaited = False
    for m in members:
        if is_async_poll_protocol_block(m.instructions):
            continue
        for i in m.instructions:
            if i.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                continue
            if prev_awaitable and i.opname == 'LOAD_CONST' and i.argval is None:
                prev_awaitable = False
                prev_call = False
                continue
            if i.opname == 'MAKE_FUNCTION':
                _mf_prev = merged[-1] if merged else None
                if (_mf_prev is not None and _mf_prev.opname == 'LOAD_CONST'
                        and self._const_code_is_async_comprehension(_mf_prev.argval)):
                    inline_pending = True
            if i.opname == 'GET_AWAITABLE' and prev_call and inline_awaited:
                prev_awaitable = True
                prev_call = False
                inline_awaited = False
                continue
            prev_awaitable = (i.opname == 'GET_AWAITABLE')
            prev_call = i.opname in _CALL_OPS
            if i.opname in _CALL_OPS:
                inline_awaited = inline_pending
                inline_pending = False
            merged.append(i)
    while merged and merged[-1].opname in _TAIL_OPS:
        merged.pop()
    if not merged:
        return None
    return self.expr_reconstructor.reconstruct(merged)


_orig = RAG.RegionASTGenerator._build_ternary_value_expr


def _patched(self, block):
    if block is not None and any(i.opname == 'GET_AWAITABLE' for i in block.instructions):
        e = _await_arm_value_expr(self, block)
        if e is not None:
            return e
    return _orig(self, block)


RAG.RegionASTGenerator._build_ternary_value_expr = _patched

import pycdc

pyc = sys.argv[1]
src = pycdc.decompile_pyc(pyc)
open(sys.argv[2], 'w', encoding='utf-8').write(src)
print('written', sys.argv[2])
