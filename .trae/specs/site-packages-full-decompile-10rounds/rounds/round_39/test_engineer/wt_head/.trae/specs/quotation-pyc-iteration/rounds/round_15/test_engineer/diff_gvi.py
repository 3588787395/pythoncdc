"""Diff bytecode for get_valuation_info"""
import sys
import types
import marshal
sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r15_decompiled.py'

with open(PYC, 'rb') as f:
    f.read(16)
    pyc_code = marshal.load(f)

with open(SRC, 'r', encoding='utf-8') as f:
    src = f.read()
src_code = compile(src, SRC, 'exec')

def collect(code, result, prefix):
    name = prefix + '.' + code.co_name if prefix else '<module>'
    result[name] = code
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, result, name)

pyc_objs = {}
collect(pyc_code, pyc_objs, '')
src_objs = {}
collect(src_code, src_objs, '')

target = '<module>.get_valuation_info'
pc = pyc_objs[target]
sc = src_objs[target]

import dis
print("=== PYC ===")
dis.dis(pc)
print("\n=== SRC ===")
dis.dis(sc)
