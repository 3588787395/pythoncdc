#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 e07 chain trace: collect/B31 gate/BSI on inner blocks + full AST."""
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
    data = open(pyc, 'rb').read()
    code = marshal.loads(data[16:])
    inners = []
    find_code(code, 'e07_async_closure', inners)
    inner = [c for c in inners if c.co_name == 'inner'][0]

    cfg = build_cfg(inner)
    gen = RAG.RegionASTGenerator(cfg, top_level_code=None)
    # find blocks by offsets
    def blk(off):
        return cfg.get_block_by_offset(off) if cfg.get_block_by_offset(off) is not None else \
            next((b for b in cfg.blocks.values() if b.start_offset == off), None)
    b2 = next((b for b in cfg.blocks.values() if any(i.offset == 30 for i in b.instructions)), None)
    b3 = next((b for b in cfg.blocks.values() if any(i.offset == 34 for i in b.instructions)), None)
    b4 = next((b for b in cfg.blocks.values() if any(i.offset == 42 for i in b.instructions)), None)
    print('b2@%s b3@%s b4@%s' % (b2.start_offset, b3.start_offset, b4.start_offset))
    print('is_poll(b3)=', RAG.is_async_poll_protocol_block(b3.instructions))

    for b, tag in ((b2, '@2'), (b3, '@3'), (b4, '@4')):
        ch = gen._collect_await_protocol_chain(b)
        if ch is None:
            print('collect(%s)=None' % tag)
        else:
            members, owner = ch
            print('collect(%s)= members %s owner @%s' % (
                tag, [m.start_offset for m in members], owner.start_offset))
            gate = gen._b31_await_chain_gate(b)
            print('   gate(%s)=%s' % (tag, json.dumps(gate, default=str)[:800]))

    ast = gen.generate()
    print('AST for inner =')
    print(json.dumps(ast, default=str)[:2500])


if __name__ == '__main__':
    main()
