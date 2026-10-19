#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 trace5: call _collect_await_protocol_chain / _b31_await_chain_gate directly."""
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

    cfg = build_cfg(co)
    gen = RAG.RegionASTGenerator(cfg, top_level_code=None)
    b42 = cfg.get_block_by_offset(42)
    b50 = cfg.get_block_by_offset(50)
    b58 = cfg.get_block_by_offset(58)
    b66 = cfg.get_block_by_offset(66)
    b98 = cfg.get_block_by_offset(98)

    print('is_async_poll_protocol_block(b50)=', RAG.is_async_poll_protocol_block(b50.instructions))
    print('is_async_poll_protocol_block(b42)=', RAG.is_async_poll_protocol_block(b42.instructions))

    for b, tag in ((b42, '@42'), (b50, '@50'), (b58, '@58')):
        ch = gen._collect_await_protocol_chain(b)
        if ch is None:
            print('collect(%s) = None' % tag)
        else:
            members, owner = ch
            print('collect(%s) = members %s owner @%s' % (
                tag, [m.start_offset for m in members], owner.start_offset))
            gate = gen._b31_await_chain_gate(b)
            print('   gate(%s) = %s' % (tag, json.dumps(gate, default=str)[:700]))

    print('cont_owner(@58)=', gen._b31_continuation_owner(b58))
    print('cont_owner(@98)=', gen._b31_continuation_owner(b98))

    # simulate merge for owner @58
    ch = gen._collect_await_protocol_chain(b58)
    if ch:
        members, owner = ch
        merged = []
        _prev_awaitable = False
        _prev_call = False
        for m in members:
            if RAG.is_async_poll_protocol_block(m.instructions):
                continue
            for i in m.instructions:
                if i.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                    continue
                if _prev_awaitable and i.opname == 'LOAD_CONST' and i.argval is None:
                    _prev_awaitable = False
                    _prev_call = False
                    continue
                _prev_awaitable = (i.opname == 'GET_AWAITABLE')
                _prev_call = i.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD')
                merged.append(i)
        print('merged =', [(i.offset, i.opname) for i in merged])
        stmts = gen._build_statements_from_instructions(merged, block=owner)
        print('BSI stmts =', json.dumps(stmts, default=str)[:900])


if __name__ == '__main__':
    main()
