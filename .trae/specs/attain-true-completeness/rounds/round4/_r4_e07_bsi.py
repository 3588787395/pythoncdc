#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 e07 BSI experiments: merged stream with/without GET_AWAITABLE."""
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
    b4 = next((b for b in cfg.blocks.values() if any(i.offset == 42 for i in b.instructions)), None)
    rv = [i for i in b4.instructions if i.opname == 'RETURN_VALUE'][0]

    base = [i for i in b2.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
    print('base:', [(i.offset, i.opname) for i in base])

    for tag, stream in (
            ('WITH_GA', [i for i in base] + [rv]),
            ('NO_GA', [i for i in base if i.opname != 'GET_AWAITABLE'] + [rv]),
            ('NO_GA_NO_NONECONST', [i for i in base if i.opname != 'GET_AWAITABLE'
                                     and not (i.opname == 'LOAD_CONST' and i.argval is None)] + [rv]),
            ('NO_GA_NO_POPTOP', [i for i in base if i.opname not in ('GET_AWAITABLE', 'POP_TOP')] + [rv]),
    ):
        gen.generated_blocks = set()
        gen.generated_offsets = set()
        stmts = gen._build_statements_from_instructions(list(stream), block=b2)
        print('BSI %s:' % tag, json.dumps(stmts, default=str)[:1200])
        print()


if __name__ == '__main__':
    main()
