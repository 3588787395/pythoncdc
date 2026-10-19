#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 e12d trace: f_await_cond_pos blocks/regions/B31 gate."""
import dis
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
    fns = []
    find_code(code, 'f_await_cond_pos', fns)
    fn = [c for c in fns if c.co_name == 'f_await_cond_pos'][0]
    dis.dis(fn)
    print()

    cfg = build_cfg(fn)
    for b in cfg.blocks.values():
        instrs = [(i.offset, i.opname, getattr(i, 'argval', None)) for i in b.instructions]
        succs = [s.start_offset for s in (b.successors or [])]
        preds = [p.start_offset for p in (getattr(b, 'predecessors', None) or [])]
        print('block@%s' % b.start_offset, instrs)
        print('   preds=%s succs=%s' % (preds, succs))

    gen = RAG.RegionASTGenerator(cfg, top_level_code=None)
    print()
    print('=== B31 gate per block (collect result + gate) ===')
    for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
        ch = gen._collect_await_protocol_chain(b)
        if ch is None:
            continue
        members, owner = ch
        print('block@%s chain members=%s owner=@%s' % (
            b.start_offset, [m.start_offset for m in members], owner.start_offset))
        g = gen._b31_await_chain_gate(b)
        if g is not None:
            print('   gate(@%s)= %s' % (b.start_offset, json.dumps(g, default=str)[:400]))


if __name__ == '__main__':
    main()
