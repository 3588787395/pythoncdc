"""Dump change_future_real_date bytecode from pyc"""
import sys, dis, types
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

result = {}
def walk(co, prefix=''):
    name = prefix + co.co_name if prefix else co.co_name
    if co.co_name == '<module>' and not prefix:
        name = '<module>'
    result[name] = co
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            sub_prefix = name + '.' if name != '<module>' else ''
            walk(const, sub_prefix)
walk(code_obj)

co = result['change_future_real_date']
print(f"co_consts: {co.co_consts}")
print(f"co_names: {co.co_names}")
print(f"co_varnames: {co.co_varnames}")
print()
for ins in dis.get_instructions(co):
    if ins.opname in ('EXTENDED_ARG', 'CACHE'):
        continue
    print(f"{ins.offset:4d} {ins.opname:30s} {ins.argrepr}")
