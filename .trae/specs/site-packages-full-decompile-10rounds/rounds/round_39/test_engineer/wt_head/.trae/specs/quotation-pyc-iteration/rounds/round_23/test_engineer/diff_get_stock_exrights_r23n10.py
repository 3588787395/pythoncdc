"""R23-N11: 调查get_stock_exrights的差异 - names_diff (replace missing)"""
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

co = find(code_obj, 'get_stock_exrights')
print(f"=== get_stock_exrights PYC co_names={co.co_names} ===")
for ins in dis.get_instructions(co):
    if ins.opname in ('EXTENDED_ARG', 'CACHE'):
        continue
    print(f"  {ins.offset:4d} {ins.opname:30s} {ins.argval!r}")

with open(SRC, 'r') as f:
    src = f.read()
match = re.search(rf'def get_stock_exrights\(.*?\n(?=\ndef |\Z|@)', src, re.DOTALL)
if match:
    print(f"\n--- 反编译源码 ---")
    print(match.group(0))

    import ast
    src_code = match.group(0)
    src_ast = ast.parse(src_code)
    compiled = compile(src_ast, '<test>', 'exec')
    for const in compiled.co_consts:
        if hasattr(const, 'co_consts') and const.co_name == 'get_stock_exrights':
            print(f"\n=== get_stock_exrights SRC co_names={const.co_names} ===")
            for ins in dis.get_instructions(const):
                if ins.opname in ('EXTENDED_ARG', 'CACHE'):
                    continue
                print(f"  {ins.offset:4d} {ins.opname:30s} {ins.argval!r}")
            break
