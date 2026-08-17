#!/usr/bin/env python3
"""Disassemble control_flow_examples original vs decompiled"""
import sys
import dis
import types
import marshal
import py_compile

sys.stdout.reconfigure(encoding='utf-8')

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

orig_cf = find_code(orig_code, 'control_flow_examples')
decomp_cf = find_code(decomp_code, 'control_flow_examples')

print("=== ORIGINAL control_flow_examples ===")
for i in dis.get_instructions(orig_cf):
    print(f"  {i.offset:4d}: {i.opname:30s} {i.argval}")

print("\n=== DECOMPILED control_flow_examples ===")
for i in dis.get_instructions(decomp_cf):
    print(f"  {i.offset:4d}: {i.opname:30s} {i.argval}")
