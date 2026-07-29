"""Dump original bytecode for problematic functions."""
import sys, types, dis
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'
module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()


def walk(co, prefix='', sink=None):
    if sink is None:
        sink = {}
    name = '<module>' if (co.co_name == '<module>' and not prefix) else prefix + co.co_name
    sink[name] = co
    sub_prefix = '' if name == '<module>' else name + '.'
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, sub_prefix, sink)
    return sink


cos = walk(code_obj)
targets = sys.argv[1:] if len(sys.argv) > 1 else ['load_bars_from_hundsun']
for t in targets:
    if t not in cos:
        print(f"NOT FOUND: {t}")
        continue
    print(f"===== {t} =====")
    dis.dis(cos[t])
    print()
