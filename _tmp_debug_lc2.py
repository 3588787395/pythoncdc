#!/usr/bin/env python3
"""Check for duplicate code object names and direct comparison"""
import sys
import types
import marshal
import py_compile
import dis

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

exec(open('testqouter/round1/base.py', encoding='utf-8').read())

with open('python_syntax_comprehensive_test.pyc', 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

py_compile.compile('python_syntax_comprehensive_testOK.py', 'python_syntax_comprehensive_testOK.pyc', doraise=True)
with open('python_syntax_comprehensive_testOK.pyc', 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)

# Find ALL <listcomp> code objects (there may be duplicates)
def find_all_codes(code, name, prefix=''):
    results = []
    if code.co_name == name:
        results.append((prefix + code.co_name, code))
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            child_prefix = prefix + code.co_name + '.'
            results.extend(find_all_codes(const, name, child_prefix))
    return results

orig_listcomps = find_all_codes(orig_code, '<listcomp>')
decomp_listcomps = find_all_codes(decomp_code, '<listcomp>')
orig_lambdas = find_all_codes(orig_code, '<lambda>')
decomp_lambdas = find_all_codes(decomp_code, '<lambda>')

print(f"Original <listcomp> count: {len(orig_listcomps)}")
for name, code in orig_listcomps:
    print(f"  {name}: {len(list(dis.get_instructions(code)))} instrs, co_varnames={code.co_varnames}")

print(f"Decompiled <listcomp> count: {len(decomp_listcomps)}")
for name, code in decomp_listcomps:
    print(f"  {name}: {len(list(dis.get_instructions(code)))} instrs, co_varnames={code.co_varnames}")

print(f"\nOriginal <lambda> count: {len(orig_lambdas)}")
for name, code in orig_lambdas:
    print(f"  {name}: {len(list(dis.get_instructions(code)))} instrs, co_varnames={code.co_varnames}, co_argcount={code.co_argcount}")

print(f"Decompiled <lambda> count: {len(decomp_lambdas)}")
for name, code in decomp_lambdas:
    print(f"  {name}: {len(list(dis.get_instructions(code)))} instrs, co_varnames={code.co_varnames}, co_argcount={code.co_argcount}")

# Direct compare first listcomp
if orig_listcomps and decomp_listcomps:
    print("\n=== Direct compare first <listcomp> ===")
    result = compare_bytecode(orig_listcomps[0][1], decomp_listcomps[0][1])
    print(f"match: {result['match']}, true_diffs: {len(result['true_diffs'])}, jump_diffs: {len(result['jump_diffs'])}")
    for d in result['true_diffs'][:5]:
        print(f"  {d}")

# Direct compare first lambda
if orig_lambdas and decomp_lambdas:
    print("\n=== Direct compare first <lambda> ===")
    result = compare_bytecode(orig_lambdas[0][1], decomp_lambdas[0][1])
    print(f"match: {result['match']}, true_diffs: {len(result['true_diffs'])}, jump_diffs: {len(result['jump_diffs'])}")
    for d in result['true_diffs'][:5]:
        print(f"  {d}")
