#!/usr/bin/env python3
"""调试脚本：打印原始pyc和反编译后py的字节码对比"""
import dis
import marshal
import sys
import types

def load_code_from_pyc(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)  # skip header
        return marshal.load(f)

def find_code_by_name(code, name_path):
    """按路径查找嵌套code对象，如 DataProcessor.validate_data"""
    parts = name_path.split('.')
    current = code
    for part in parts:
        if part == '<module>':
            continue
        found = None
        for const in current.co_consts:
            if isinstance(const, types.CodeType) and const.co_name == part:
                found = const
                break
        if found is None:
            return None
        current = found
    return current

def print_instructions(code, label):
    print(f"\n{'='*60}")
    print(f"{label}: {code.co_name}")
    print(f"{'='*60}")
    for instr in dis.get_instructions(code):
        print(f"  {instr.offset:4d} {instr.opname:30s} {instr.arg if instr.arg is not None else '':>4} {instr.argval if instr.argval is not None else ''}")

pyc_path = sys.argv[1] if len(sys.argv) > 1 else 'decompiler_test_comprehensive.cpython-311.pyc'
py_path = sys.argv[2] if len(sys.argv) > 2 else 'decompiler_test_comprehensive_decompiled.py'

orig_code = load_code_from_pyc(pyc_path)

with open(py_path, 'r', encoding='utf-8') as f:
    source = f.read()
decomp_code = compile(source, py_path, 'exec')

# 查找需要对比的函数
targets = [
    'DataProcessor.validate_data',
    'DataProcessor.exception_handling_complex', 
    'DataProcessor.final_integration_test',
]

for target in targets:
    orig = find_code_by_name(orig_code, target)
    decomp = find_code_by_name(decomp_code, target)
    if orig:
        print_instructions(orig, "ORIGINAL")
    if decomp:
        print_instructions(decomp, "DECOMPILED")
