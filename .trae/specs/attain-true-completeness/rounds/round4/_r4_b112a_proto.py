#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 B112-a prototype: async-gen yield-of-await chain gate (monkeypatch, offline test).

用法: python _r4_b112a_proto.py <pyc> <qualname-substr>
"""
import io
import json
import marshal
import os
import sys
import types as pytypes

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import build_cfg
from core.cfg import region_ast_generator as RAG

_NOISE = ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')
_STORE_OPS = ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')


def b112_gate(self, block):
    def _denoise(b):
        return [i for i in b.instructions if i.opname not in _NOISE]

    def _is_landing(b):
        d = _denoise(b)
        return (len(d) == 3 and d[0].opname == 'ASYNC_GEN_WRAP'
                and d[1].opname == 'YIELD_VALUE'
                and d[2].opname == 'POP_TOP')

    def _poll_targeting(cur):
        out = []
        for pred in (getattr(cur, 'predecessors', None) or []):
            if pred is cur:
                continue
            if not RAG.is_async_poll_protocol_block(pred.instructions):
                continue
            for i in pred.instructions:
                if i.opname == 'SEND' and i.argval is not None:
                    if self.cfg.get_block_by_offset(i.argval) is cur:
                        out.append(pred)
                    break
        return out

    def _setup_of(p):
        out = []
        for pred in (getattr(p, 'predecessors', None) or []):
            if pred is p:
                continue
            if p in (getattr(pred, 'successors', None) or []):
                if any(i.opname == 'GET_AWAITABLE' for i in pred.instructions):
                    out.append(pred)
        return out

    owner = None
    poll = None
    if _is_landing(block):
        owner = block
        polls = _poll_targeting(block)
        if len(polls) != 1:
            return None
        poll = polls[0]
    elif RAG.is_async_poll_protocol_block(block.instructions):
        tgt = None
        for i in block.instructions:
            if i.opname == 'SEND' and i.argval is not None:
                tgt = self.cfg.get_block_by_offset(i.argval)
                break
        if tgt is None or not _is_landing(tgt):
            return None
        owner, poll = tgt, block
    else:
        for succ in block.successors:
            if succ is block:
                continue
            if not RAG.is_async_poll_protocol_block(succ.instructions):
                continue
            t2 = None
            for i in succ.instructions:
                if i.opname == 'SEND' and i.argval is not None:
                    t2 = self.cfg.get_block_by_offset(i.argval)
                    break
            if t2 is not None and _is_landing(t2):
                owner, poll = t2, succ
                break
        if owner is None:
            return None
    setups = _setup_of(poll)
    if len(setups) != 1:
        return None
    if block is not owner:
        print('[B112-defer] block@%s (owner@%s)' % (block.start_offset, owner.start_offset))
        return []
    setup = setups[0]
    merged = []
    _prev_awaitable = False
    for m in (setup, owner):
        for i in m.instructions:
            if i.opname in _NOISE:
                continue
            if _prev_awaitable and i.opname == 'LOAD_CONST' and i.argval is None:
                _prev_awaitable = False
                continue
            _prev_awaitable = (i.opname == 'GET_AWAITABLE')
            merged.append(i)
    if merged and merged[0].opname in _STORE_OPS and _poll_targeting(setup):
        merged = merged[1:]
    print('[B112-merge] setup@%s poll@%s owner@%s merged=%s' % (
        setup.start_offset, poll.start_offset, owner.start_offset,
        [(i.offset, i.opname) for i in merged]))
    stmts = self._build_statements_from_instructions(merged, block=owner)
    print('[B112-stmts]', json.dumps(stmts, default=str)[:700])
    if not stmts:
        return None
    last = stmts[-1]
    if not (last.get('type') == 'Expr'
            and (last.get('value') or {}).get('type') == 'Yield'):
        return None
    for m in (setup, poll, owner):
        self.generated_blocks.add(m)
        self.generated_offsets.add(m.start_offset)
        for i in m.instructions:
            self.generated_offsets.add(i.offset)
    return stmts


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, pytypes.CodeType):
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
    print('code =', co.co_qualname)

    orig_body = RAG.RegionASTGenerator._generate_block_statements_body

    def body(self, block, _cjb_parent=None):
        if block in self.generated_blocks:
            return []
        _meaningful = [i for i in block.instructions
                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
        if _meaningful and all(i.offset in self.generated_offsets for i in _meaningful):
            return []
        g = b112_gate(self, block)
        if g is not None:
            return g
        return orig_body(self, block, _cjb_parent)

    RAG.RegionASTGenerator._generate_block_statements_body = body

    cfg = build_cfg(co)
    gen = RAG.RegionASTGenerator(cfg, top_level_code=None)
    ast = gen.generate()
    print('AST:')
    print(json.dumps(ast, default=str)[:3500])


if __name__ == '__main__':
    main()
