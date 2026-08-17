#!/usr/bin/env python3
"""Debug listcomp and lambda mismatches"""
import sys
import dis
import types
import marshal
import py_compile

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

with open('python_syntax_comprehensive_test.pyc', 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

py_compile.compile('python_syntax_comprehensive_testOK.py', 'python_syntax_comprehensive_testOK.pyc', doraise=True)
with open('python_syntax_comprehensive_testOK.pyc', 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)

def find_code(code, name):
    for const in code.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == name:
            return const
    return None

# Listcomp
print("=== <listcomp> ===")
orig_lc = find_code(orig_code, '<listcomp>')
decomp_lc = find_code(decomp_code, '<listcomp>')
if orig_lc and decomp_lc:
    print("Original:")
    for i in dis.get_instructions(orig_lc):
        print(f"  {i.offset:4d}: {i.opname:30s} {i.argval}")
    print("Decompiled:")
    for i in dis.get_instructions(decomp_lc):
        print(f"  {i.offset:4d}: {i.opname:30s} {i.argval}")

# Lambda
print("\n=== <lambda> ===")
orig_lm = find_code(orig_code, '<lambda>')
decomp_lm = find_code(decomp_code, '<lambda>')
if orig_lm and decomp_lm:
    print("Original:")
    for i in dis.get_instructions(orig_lm):
        print(f"  {i.offset:4d}: {i.opname:30s} {i.argval}")
    print("Decompiled:")
    for i in dis.get_instructions(decomp_lm):
        print(f"  {i.offset:4d}: {i.opname:30s} {i.argval}")
