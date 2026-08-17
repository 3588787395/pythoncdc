#!/usr/bin/env python3
"""Round 07: Show decompiled exception_handling_examples and diff bytecode."""
import sys, os, dis, types, marshal, ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from pycdc import decompile_pyc

PYC_PATH = str(PROJECT_ROOT / 'python_syntax_comprehensive_test.pyc')

def load_code_from_pyc(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        code = marshal.load(f)
    return code

def collect_all_code_objects(code, prefix=''):
    from collections import OrderedDict
    result = OrderedDict()
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
    target_name = '<module>.exception_handling_examples'
    target_code = all_codes[target_name]
    
    # Decompile
    source = decompile_pyc(PYC_PATH)
    
    # Find the function in the source
    lines = source.split('\n')
    in_func = False
    func_lines = []
    for line in lines:
        if line.startswith('def exception_handling_examples'):
            in_func = True
        if in_func:
            func_lines.append(line)
            if line.strip() == '' and len(func_lines) > 5:
                break
    
    print("=== Decompiled exception_handling_examples ===")
    print('\n'.join(func_lines))
    
    # Compile the function and compare bytecode
    print("\n=== Original bytecode ===")
    dis.dis(target_code)
    
    # Compile decompiled function
    func_source = '\n'.join(func_lines)
    try:
        mod = ast.parse(func_source)
        compiled = compile(mod, '<decompiled>', 'exec')
        # Get the function code object
        for const in compiled.co_consts:
            if isinstance(const, types.CodeType) and const.co_name == 'exception_handling_examples':
                print("\n=== Decompiled bytecode ===")
                dis.dis(const)
                break
    except Exception as e:
        print(f"\nCompile error: {e}")

if __name__ == '__main__':
    main()
