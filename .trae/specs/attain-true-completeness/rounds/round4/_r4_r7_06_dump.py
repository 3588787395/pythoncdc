#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 B47 dump: dis + CFG blocks for r7_06 ternary/await functions."""
import dis
import io
import marshal
import os
import sys
import types

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

pyc = r'test_repros/round7/r7_06_ternary_lambda_await.pyc'
data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])

targets = {'t_await_ternary_branches', 't_await_assign_ternary', 't_await_deep_ternary'}
for const in code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name in targets:
        print('=' * 70)
        print('FUNC', const.co_name)
        dis.dis(const, file=sys.stdout, depth=0)
        print('-' * 70)
        instrs = list(dis.get_instructions(const))
        leaders = {0}
        for ins in instrs:
            if ins.opname.startswith('POP_JUMP') or ins.opname == 'JUMP_FORWARD' or ins.opname == 'JUMP_BACKWARD' or ins.opname == 'FOR_ITER' or ins.opname == 'SEND':
                if isinstance(ins.argval, int):
                    leaders.add(ins.argval)
            if ins.opname in ('JUMP_BACKWARD_NO_INTERRUPT',):
                pass
        leaders = sorted(leaders)
        bounds = leaders + [len(instrs)]
        for li in range(len(leaders)):
            lo = leaders[li]
            hi = bounds[li + 1]
            seg = [i for i in instrs if lo <= i.offset < hi]
            if not seg:
                continue
            offs = [s.offset for s in seg]
            jumps = [f'{s.opname}:{s.argval}' for s in seg if s.opname.startswith(('POP_JUMP', 'JUMP', 'SEND', 'FOR_ITER'))]
            print(f"block@~{lo}: offs={offs[0]}..{offs[-1]} -> {jumps}")
