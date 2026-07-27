"""Dump bytecode for get_valuation_info from quotation.pyc"""
import sys
import types
import marshal
import dis

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'

with open(PYC, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

result = {}
def _collect(c, result, prefix):
    name = prefix + '.' + c.co_name if prefix else '<module>'
    result[name] = c
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            _collect(k, result, name)

_collect(code, result, '')

fn = result['<module>.get_valuation_info']
print(f"=== get_valuation_info bytecode ===")
bc = fn
print(f"co_consts: {bc.co_consts}")
print(f"co_names: {bc.co_names}")
print(f"co_varnames: {bc.co_varnames}")
print()
dis.dis(fn)
