#!/usr/bin/env python3

import sys
import dis
import py_compile
import marshal
import types

def load_pyc_file(filepath):
    """Load the code object from a .pyc file"""
    with open(filepath, 'rb') as f:
        magic = f.read(4)
        bit_field = f.read(4)
        timestamp = f.read(4)
        size = f.read(4)
        code = marshal.load(f)
    return code

def compare_pyc_files(orig_pyc, decomp_py):
    """Compare bytecode between original .pyc and decompiled Python file"""
    print("=== Loading original .pyc file ===")
    orig_code = load_pyc_file(orig_pyc)
    orig_bytecode_constants = {}
    for const in orig_code.co_consts:
        if hasattr(const, 'co_consts'):
            for c2 in const.co_consts:
                if hasattr(c2, 'co_consts'):
                    for c3 in c2.co_consts:
                        if hasattr(c3, 'co_consts'):
                            for c4 in c3.co_consts:
                                if hasattr(c4, 'co_consts'):
                                    for c5 in c4.co_consts:
                                        if hasattr(c5, 'co_consts'):
                                            for c6 in c5.co_consts:
                                                if hasattr(c6, 'co_consts'):
                                                    for c7 in c6.co_consts:
                                                        if hasattr(c7, 'co_consts'):
                                                            for c8 in c7.co_consts:
                                                                if hasattr(c8, 'co_consts'):
                                                                    for c9 in c8.co_consts:
                                                                        pass
    orig_funcs = {}
    for const in orig_code.co_consts:
        if isinstance(const, types.CodeType):
            orig_funcs[const.co_name] = const
            for c2 in const.co_consts:
                if isinstance(c2, types.CodeType):
                    orig_funcs[c2.co_name] = c2
                    for c3 in c2.co_consts:
                        if isinstance(c3, types.CodeType):
                            orig_funcs[c3.co_name] = c3
                            for c4 in c3.co_consts:
                                if isinstance(c4, types.CodeType):
                                    orig_funcs[c4.co_name] = c4
                                    for c5 in c4.co_consts:
                                        if isinstance(c5, types.CodeType):
                                            orig_funcs[c5.co_name] = c5
    print("Found functions:", list(orig_funcs.keys()))
    print()

    print("=== Compiling decompiled Python file ===")
    py_compile.compile(decomp_py, 'temp_compare.pyc')
    decomp_code = load_pyc_file('temp_compare.pyc')
    decomp_funcs = {}
    for const in decomp_code.co_consts:
        if isinstance(const, types.CodeType):
            decomp_funcs[const.co_name] = const
            for c2 in const.co_consts:
                if isinstance(c2, types.CodeType):
                    decomp_funcs[c2.co_name] = c2
                    for c3 in c2.co_consts:
                        if isinstance(c3, types.CodeType):
                            decomp_funcs[c3.co_name] = c3
                            for c4 in c3.co_consts:
                                if isinstance(c4, types.CodeType):
                                    decomp_funcs[c4.co_name] = c4
                                    for c5 in c4.co_consts:
                                        if isinstance(c5, types.CodeType):
                                            decomp_funcs[c5.co_name] = c5
    print("Found functions:", list(decomp_funcs.keys()))
    print()

    print("=== Comparing functions ===")
    pass_count = 0
    fail_count = 0
    failed_funcs = []

    for func_name in orig_funcs:
        if func_name not in decomp_funcs:
            print(f"FAIL: {func_name} missing in decompiled")
            fail_count += 1
            failed_funcs.append(func_name)
            continue
        orig_f = orig_funcs[func_name]
        decomp_f = decomp_funcs[func_name]
        orig_ops = [i.opname for i in dis.get_instructions(orig_f)]
        decomp_ops = [i.opname for i in dis.get_instructions(decomp_f)]
        if orig_ops == decomp_ops:
            print(f"✓ {func_name}")
            pass_count += 1
        else:
            print(f"✗ {func_name}")
            fail_count += 1
            failed_funcs.append(func_name)

    for func_name in decomp_funcs:
        if func_name not in orig_funcs:
            print(f"INFO: {func_name} only in decompiled (e.g., main)")

    total = pass_count + fail_count
    rate = pass_count / total * 100 if total > 0 else 0
    print()
    print(f"=== Summary ===")
    print(f"Pass: {pass_count}/{total} ({rate:.2f}%)")
    print(f"Fail: {fail_count}/{total}")
    if failed_funcs:
        print(f"Failed: {failed_funcs}")
    return pass_count, fail_count, failed_funcs

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python compare_current.py <original.pyc> <decompiled.py>")
        sys.exit(1)
    orig_pyc = sys.argv[1]
    decomp_py = sys.argv[2]
    compare_pyc_files(orig_pyc, decomp_py)
