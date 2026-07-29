"""R23-N11: 调查change_future_real_date的差异"""
import sys
import dis
import types
import re

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r23_decompiled.py'

from core.pyc_loader_v2 import load_pyc_file_v2

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

def find(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if hasattr(c, 'co_consts'):
            r = find(c, name)
            if r: return r
    return None

co = find(code_obj, 'change_future_real_date')
print(f"=== change_future_real_date PYC (len={len(list(dis.get_instructions(co)))}) ===")
for ins in dis.get_instructions(co):
    if ins.opname in ('EXTENDED_ARG', 'CACHE'):
        continue
    print(f"  {ins.offset:4d} {ins.opname:30s} {ins.argval!r}")

with open(SRC, 'r') as f:
    src = f.read()
match = re.search(rf'def change_future_real_date\(.*?\n(?=\ndef |\Z|@)', src, re.DOTALL)
if match:
    print(f"\n--- 反编译源码 ---")
    print(match.group(0))
