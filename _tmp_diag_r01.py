#!/usr/bin/env python3
"""Diagnose Round 01 defects: show original vs decompiled source for each DEFECT-REPRO."""
import sys, os, dis, types, marshal, py_compile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
from testqouter.round1.base import decompile_pyc, compare_bytecode

REPRO_DIR = PROJECT_ROOT / '.trae' / 'specs' / 'region-comprehensive-pyc-10rounds' / 'rounds' / 'round_01' / 'test_engineer' / 'minimal_repros'

defects = [
    'repro_04_cf2_while_else_break',
    'repro_07_te1_try_except_else_finally',
    'repro_10_as1_async_await_body',
]

for name in defects:
    pyc_path = REPRO_DIR / f'{name}.pyc'
    py_path = REPRO_DIR / f'{name}.py'

    print(f"\n{'='*70}")
    print(f"DEFECT: {name}")
    print(f"{'='*70}")

    # Show original source
    with open(py_path, 'r', encoding='utf-8') as f:
        print("--- ORIGINAL SOURCE ---")
        print(f.read())

    # Show decompiled source
    try:
        decomp = decompile_pyc(str(pyc_path))
        print("--- DECOMPILED SOURCE ---")
        print(decomp)
    except Exception as e:
        print(f"Decompile error: {e}")

    # Show bytecode diff for the main function
    with open(pyc_path, 'rb') as f:
        f.read(16)
        orig_code = marshal.load(f)

    decomp_code = compile(decomp, '<decompiled>', 'exec')

    def collect_codes(code, prefix=''):
        result = {prefix + code.co_name: code}
        for const in code.co_consts:
            if isinstance(const, types.CodeType):
                child_prefix = prefix + code.co_name + '.'
                result.update(collect_codes(const, child_prefix))
        return result

    orig_all = collect_codes(orig_code)
    decomp_all = collect_codes(decomp_code)

    for func_name in orig_all:
        if func_name in decomp_all:
            result = compare_bytecode(orig_all[func_name], decomp_all[func_name])
            if not result['match']:
                print(f"\n--- BYTECODE DIFF: {func_name} ---")
                print(f"true_diffs: {len(result['true_diffs'])}, jump_diffs: {len(result['jump_diffs'])}")
                print(f"orig_ops ({len(result['orig_ops'])}): {result['orig_ops'][:20]}...")
                print(f"decomp_ops ({len(result['decomp_ops'])}): {result['decomp_ops'][:20]}...")
                for td in result['true_diffs'][:8]:
                    print(f"  TD: {td}")
                for jd in result['jump_diffs'][:5]:
                    print(f"  JD: {jd}")
