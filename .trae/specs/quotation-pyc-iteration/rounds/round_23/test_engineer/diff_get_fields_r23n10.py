"""R23-N11: 调查get_fields的差异"""
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

co = find(code_obj, 'get_fields')
print(f"=== get_fields PYC co_names={co.co_names} ===")

with open(SRC, 'r') as f:
    src = f.read()
match = re.search(rf'def get_fields\(.*?\n(?=\ndef |\Z|@)', src, re.DOTALL)
if match:
    print(f"\n--- 反编译源码 ---")
    print(match.group(0))
