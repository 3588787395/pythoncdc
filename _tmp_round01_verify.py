#!/usr/bin/env python3
"""Round 01 verification: decompile + bytecode diff for python_syntax_comprehensive_test.pyc"""
import sys
import os
import dis
import types
import marshal
import struct

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

# Import comparison functions from testqouter/round1/base.py
exec(open('testqouter/round1/base.py', encoding='utf-8').read())


def load_pyc_code(pyc_path):
    """Load code object from .pyc file"""
    with open(pyc_path, 'rb') as f:
        magic = f.read(4)
        flags = struct.unpack('<I', f.read(4))[0]
        # Skip timestamp/hash (depends on flags)
        if flags & 1:  # PEP 552 hash-based
            f.read(8)
        else:
            f.read(8)  # timestamp + source size
        code = marshal.load(f)
    return code


def compare_all_functions(orig_code, decomp_code):
    """Recursively compare all code objects (functions, classes, etc.)"""
    results = []

    def _collect_codes(code, prefix=''):
        """Collect all code objects with their qualified names"""
        codes = [(prefix + code.co_name, code)]
        for const in code.co_consts:
            if isinstance(const, types.CodeType):
                child_prefix = prefix + code.co_name + '.'
                codes.extend(_collect_codes(const, child_prefix))
        return codes

    orig_codes = _collect_codes(orig_code)
    decomp_codes = _collect_codes(decomp_code)

    # Create lookup by name
    decomp_lookup = {name: code for name, code in decomp_codes}

    total = len(orig_codes)
    matched = 0
    mismatches = []

    for name, orig_func_code in orig_codes:
        if name in decomp_lookup:
            result = compare_bytecode(orig_func_code, decomp_lookup[name])
            if result['match']:
                matched += 1
            else:
                # Get first diff for summary
                first_diff = None
                if result['true_diffs']:
                    first_diff = result['true_diffs'][0]
                elif result['jump_diffs']:
                    first_diff = result['jump_diffs'][0]

                mismatches.append({
                    'name': name,
                    'true_diffs': len(result['true_diffs']),
                    'jump_diffs': len(result['jump_diffs']),
                    'first_diff': first_diff,
                })
        else:
            mismatches.append({
                'name': name,
                'true_diffs': -1,
                'jump_diffs': -1,
                'first_diff': {'type': 'missing_function'},
            })

    return total, matched, mismatches


# Load original pyc
orig_code = load_pyc_code('python_syntax_comprehensive_test.pyc')

# Load decompiled OK.py
import py_compile
py_compile.compile('python_syntax_comprehensive_testOK.py',
                   'python_syntax_comprehensive_testOK.pyc',
                   doraise=True)
decomp_code = load_pyc_code('python_syntax_comprehensive_testOK.pyc')

# Compare
total, matched, mismatches = compare_all_functions(orig_code, decomp_code)
rate = matched / total * 100 if total > 0 else 0

print(f"=== Round 01 Bytecode Comparison ===")
print(f"Total functions: {total}")
print(f"Matched: {matched}")
print(f"Mismatches: {len(mismatches)}")
print(f"Success rate: {rate:.2f}%")
print()
for m in mismatches:
    print(f"  {m['name']}: {m['true_diffs']}td/{m['jump_diffs']}jd")
    if m.get('first_diff'):
        fd = m['first_diff']
        print(f"    first_diff: {fd}")
