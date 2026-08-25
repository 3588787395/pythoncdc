#!/usr/bin/env python3
"""R100: disassemble check_strategy to understand control flow"""
import sys, marshal, dis, types
sys.path.insert(0, '.')

pyc_path = 'site-packages/IQCommon/api/check_strategy.pyc'
code = marshal.loads(open(pyc_path, 'rb').read()[16:])
funcs = [c for c in code.co_consts if isinstance(c, types.CodeType)]
cs = [f for f in funcs if f.co_name == 'check_strategy'][0]

print('=== check_strategy bytecode (orig) ===')
for instr in dis.get_instructions(cs):
    print(f'  {instr.offset:4d} {instr.opname:30s} {instr.argval}')
