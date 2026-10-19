#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 e07 reconstructor experiments: async comprehension call stream."""
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
    b2 = next((b for b in cfg.blocks.values() if any(i.offset == 30 for i in b.instructions)), None)
    print('block@2 instrs:', [(i.offset, i.opname) for i in b2.instructions])

    rc = gen.expr_reconstructor
    full = [i for i in b2.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')]
    print('stream:', [(i.offset, i.opname) for i in full])

    # b: with GET_AWAITABLE
    rc.reset()
    r1 = rc.reconstruct(list(full))
    print('WITH GA:', json.dumps(r1, default=str)[:900])

    # c: without GET_AWAITABLE
    nog = [i for i in full if i.opname != 'GET_AWAITABLE']
    rc.reset()
    r2 = rc.reconstruct(list(nog))
    print('NO GA:', json.dumps(r2, default=str)[:900])

    # d: without GA and without LOAD_CONST None
    nog2 = [i for i in nog if not (i.opname == 'LOAD_CONST' and i.argval is None)]
    rc.reset()
    r3 = rc.reconstruct(list(nog2))
    print('NO GA NO None:', json.dumps(r3, default=str)[:900])

    # e: BSI on merged-with-GA stream
    bsi = gen._build_statements_from_instructions(list(full) + [i for i in cfg.blocks.values() if any(x.offset == 42 for x in i.instructions)][0].instructions[0], block=b2)
    print('BSI WITH GA:', json.dumps(bsi, default=str)[:900])


if __name__ == '__main__':
    main()
