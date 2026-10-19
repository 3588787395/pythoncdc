#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 synth b112a: compare CFG builds for s_plain vs s_cond_host."""
import io
import marshal
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = open(r'test_repros/round4/rec1_synth_b112a_asyncgen.pyc', 'rb').read()
code = marshal.loads(data[16:])

funcs = {c.co_name: c for c in code.co_consts if isinstance(c, types.CodeType)}

from core.cfg.cfg_builder import CFGBuilder

for name in ('s_plain', 's_cond_host'):
    f = funcs.get(name)
    print('=' * 70)
    print('FUNC', name)
    if f is None:
        print('  MISSING')
        continue
    try:
        cfg = CFGBuilder().build(f)
        print('  CFG ok, blocks:')
        for key in cfg.blocks:
            b = cfg.get_block_by_offset(key) if isinstance(key, int) else key
            print(f'    @{b.start_offset} offs={[i.offset for i in b.instructions]} succs={[s.start_offset for s in b.successors]}')
    except Exception as e:
        import traceback
        print('  CFG BUILD EXCEPTION:', type(e).__name__, e)
        traceback.print_exc(file=sys.stdout)
