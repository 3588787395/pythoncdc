#!/usr/bin/env python3

import sys
import dis
import py_compile
import marshal
import types

def load_pyc_file(filepath):
    with open(filepath, 'rb') as f:
        magic = f.read(4)
        bit_field = f.read(4)
        timestamp = f.read(4)
        size = f.read(4)
        code = marshal.load(f)
    return code

def extract_all_functions(code):
    funcs = {}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            funcs[const.co_name] = const
            for c2 in const.co_consts:
                if isinstance(c2, types.CodeType):
                    funcs[c2.co_name] = c2
                    for c3 in c2.co_consts:
                        if isinstance(c3, types.CodeType):
                            funcs[c3.co_name] = c3
                            for c4 in c3.co_consts:
                                if isinstance(c4, types.CodeType):
                                    funcs[c4.co_name] = c4
                                    for c5 in c4.co_consts:
                                        if isinstance(c5, types.CodeType):
                                            funcs[c5.co_name] = c5
    return funcs

def compare_pyc_files(orig_pyc, decomp_py):
    print("=== Loading original .pyc file ===")
    orig_code = load_pyc_file(orig_pyc)
    orig_funcs = extract_all_functions(orig_code)
    print(f"Found {len(orig_funcs)} functions")
    print("Function names:", ', '.join(sorted(orig_funcs.keys())))
    print()

    print("=== Compiling and loading decompiled Python file ===")
    try:
        py_compile.compile(decomp_py, 'temp_compare.pyc')
    except Exception as e:
        print(f"Compile error: {e}")
        return 0, 0, []
    decomp_code = load_pyc_file('temp_compare.pyc')
    decomp_funcs = extract_all_functions(decomp_code)
    print(f"Found {len(decomp_funcs)} functions")
    print("Function names:", ', '.join(sorted(decomp_funcs.keys())))
    print()

    print("=== Comparing functions ===")
    pass_count = 0
    fail_count = 0
    failed_funcs = []

    for func_name in sorted(orig_funcs.keys()):
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
            print(f"PASS {func_name}")
            pass_count += 1
        else:
            print(f"FAIL {func_name}")
            fail_count += 1
            failed_funcs.append(func_name)

    print()
    print("=== Additional functions in decompiled ===")
    for func_name in sorted(decomp_funcs.keys()):
        if func_name not in orig_funcs:
            print(f"  {func_name} (only in decompiled)")

    total = pass_count + fail_count
    rate = pass_count / total * 100 if total > 0 else 0
    print()
    print("=== Summary ===")
    print(f"Pass: {pass_count}/{total} ({rate:.2f}%)")
    print(f"Fail: {fail_count}/{total}")
    if failed_funcs:
        print(f"Failed functions: {', '.join(failed_funcs)}")
    return pass_count, fail_count, failed_funcs

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python quick_test.py <original.pyc> <decompiled.py>")
        sys.exit(1)
    orig_pyc = sys.argv[1]
    decomp_py = sys.argv[2]
    compare_pyc_files(orig_pyc, decomp_py)
