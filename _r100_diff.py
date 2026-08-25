#!/usr/bin/env python3
"""R100 测试工程师：分析 check_strategy.pyc 字节码差异"""
import sys, marshal, dis, types, ast, json
sys.path.insert(0, '.')
import pycdc
from testqouter.round1.base import compare_bytecode

pyc_path = 'site-packages/IQCommon/api/check_strategy.pyc'
code = marshal.loads(open(pyc_path, 'rb').read()[16:])
funcs = [c for c in code.co_consts if isinstance(c, types.CodeType)]
cs = [f for f in funcs if f.co_name == 'check_strategy'][0]

decompiled = pycdc.decompile_pyc(pyc_path)
tree = ast.parse(decompiled)
ok_code = compile(tree, '<ok>', 'exec')
ok_funcs = [c for c in ok_code.co_consts if isinstance(c, types.CodeType)]
ok_cs = [f for f in ok_funcs if f.co_name == 'check_strategy'][0]

orig = list(dis.get_instructions(cs))
decomp = list(dis.get_instructions(ok_cs))
print(f'orig instrs: {len(orig)}, decomp instrs: {len(decomp)}')

# Print first 30 differences side by side
print('\n=== First 30 differences (side by side) ===')
max_len = max(len(orig), len(decomp))
shown = 0
for i in range(max_len):
    o = orig[i] if i < len(orig) else None
    d = decomp[i] if i < len(decomp) else None
    o_str = f'{o.opname} {o.argval}' if o else '---'
    d_str = f'{d.opname} {d.argval}' if d else '---'
    if o_str != d_str:
        print(f'  [{i:3d}] orig: {o_str:40s} | decomp: {d_str}')
        shown += 1
        if shown >= 30:
            break

# Also show the decompiled source
print('\n=== Decompiled check_strategy source ===')
print(decompiled)
