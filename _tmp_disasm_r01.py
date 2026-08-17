#!/usr/bin/env python3
"""Disassemble mismatched functions from python_syntax_comprehensive_test.pyc for Round 01 analysis."""
import dis, marshal, struct, types, sys, os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

PYC_PATH = str(PROJECT_ROOT / 'python_syntax_comprehensive_test.pyc')

def load_code_from_pyc(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(4)  # magic
        f.read(4)  # flags
        f.read(8)  # timestamp + size
        return marshal.load(f)

def collect_all_code_objects(code, prefix=''):
    result = {}
    name = prefix + code.co_name if prefix else code.co_name
    result[name] = code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            child_prefix = prefix + code.co_name + '.' if prefix else code.co_name + '.'
            result.update(collect_all_code_objects(const, child_prefix))
    return result

def main():
    orig_code = load_code_from_pyc(PYC_PATH)
    all_codes = collect_all_code_objects(orig_code)

    targets = ['<module>', 'control_flow_examples', 'exception_handling_examples', 'multiple_coroutines', 'complex_expressions']

    for target in targets:
        if target in all_codes:
            code = all_codes[target]
            print(f"\n{'='*70}")
            print(f"ORIGINAL BYTECODE: {target}")
            print(f"{'='*70}")
            dis.dis(code)
            print()

    # Also disassemble decompiled
    from testqouter.round1.base import decompile_pyc
    source = decompile_pyc(PYC_PATH)
    decomp_code = compile(source, '<decompiled>', 'exec')
    decomp_all = collect_all_code_objects(decomp_code)

    for target in targets:
        if target in decomp_all:
            code = decomp_all[target]
            print(f"\n{'='*70}")
            print(f"DECOMPILED BYTECODE: {target}")
            print(f"{'='*70}")
            dis.dis(code)
            print()

if __name__ == '__main__':
    main()
