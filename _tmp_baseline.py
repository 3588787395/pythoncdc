#!/usr/bin/env python3
"""Baseline: decompile python_syntax_comprehensive_test.pyc + bytecode diff."""

import sys, os, dis, types, marshal, struct, py_compile, json, io, time
from pathlib import Path
from collections import OrderedDict

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from testqouter.round1.base import compare_bytecode, decompile_pyc, _filter_noise_instrs, _normalize_argval

PYC_PATH = str(PROJECT_ROOT / 'python_syntax_comprehensive_test.pyc')
OK_PATH = str(PROJECT_ROOT / 'python_syntax_comprehensive_testOK.py')

def load_code_from_pyc(pyc_path):
    with open(pyc_path, 'rb') as f:
        magic = f.read(4)
        flags = struct.unpack('<I', f.read(4))[0]
        f.read(8)  # timestamp + size
        code = marshal.load(f)
    return code

def collect_all_code_objects(code, prefix=''):
    """Recursively collect all code objects from a module."""
    result = OrderedDict()
    name = prefix + code.co_name if prefix else code.co_name
    result[name] = code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            child_prefix = prefix + code.co_name + '.' if prefix else code.co_name + '.'
            result.update(collect_all_code_objects(const, child_prefix))
    return result

def main():
    print("=" * 70)
    print("BASELINE: python_syntax_comprehensive_test.pyc")
    print("=" * 70)

    # 1. Load original code
    orig_code = load_code_from_pyc(PYC_PATH)
    orig_all = collect_all_code_objects(orig_code)
    print(f"Original code objects: {len(orig_all)}")
    for name in orig_all:
        print(f"  - {name}")

    # 2. Decompile
    print("\n--- Decompiling ---")
    t0 = time.time()
    try:
        source = decompile_pyc(PYC_PATH)
        print(f"Decompiled in {time.time()-t0:.1f}s, {len(source)} chars")
    except Exception as e:
        print(f"Decompile FAILED: {e}")
        import traceback; traceback.print_exc()
        return

    # 3. Compile decompiled source
    print("\n--- Compiling decompiled source ---")
    try:
        decomp_code = compile(source, '<decompiled>', 'exec')
        print("Compile OK")
    except SyntaxError as e:
        print(f"Compile FAILED (SyntaxError): {e}")
        # Still try to get what we can
        return

    decomp_all = collect_all_code_objects(decomp_code)
    print(f"Decompiled code objects: {len(decomp_all)}")

    # 4. Bytecode diff per function
    print("\n--- Bytecode Diff ---")
    matched = 0
    total = 0
    mismatches = []

    for name, orig_func_code in orig_all.items():
        total += 1
        if name in decomp_all:
            result = compare_bytecode(orig_func_code, decomp_all[name])
            if result['match']:
                matched += 1
                print(f"  [MATCH] {name}")
            else:
                true_diffs = len(result['true_diffs'])
                jump_diffs = len(result['jump_diffs'])
                print(f"  [MISMATCH] {name}: {true_diffs} true_diffs, {jump_diffs} jump_diffs")
                if true_diffs > 0:
                    for td in result['true_diffs'][:3]:
                        print(f"    -> {td}")
                mismatches.append({
                    'name': name,
                    'true_diffs': true_diffs,
                    'jump_diffs': jump_diffs,
                    'details': result['true_diffs'][:5],
                })
        else:
            print(f"  [MISSING] {name}")
            mismatches.append({
                'name': name,
                'true_diffs': -1,
                'jump_diffs': 0,
                'details': 'Function missing in decompiled code',
            })

    success_rate = matched / total * 100 if total > 0 else 0
    print(f"\n{'=' * 70}")
    print(f"RESULTS: {matched}/{total} matched = {success_rate:.2f}%")
    print(f"Mismatches: {len(mismatches)}")
    for m in mismatches:
        print(f"  - {m['name']}: true_diffs={m['true_diffs']}, jump_diffs={m['jump_diffs']}")
    print(f"{'=' * 70}")

    # Save report
    report_dir = PROJECT_ROOT / '.trae' / 'specs' / 'region-comprehensive-pyc-10rounds' / 'baseline'
    report_dir.mkdir(parents=True, exist_ok=True)
    with open(report_dir / 'baseline_report.md', 'w', encoding='utf-8') as f:
        f.write(f"# Baseline Report: python_syntax_comprehensive_test.pyc\n\n")
        f.write(f"## Summary\n")
        f.write(f"- Total functions: {total}\n")
        f.write(f"- Matched: {matched}\n")
        f.write(f"- Success rate: {success_rate:.2f}%\n")
        f.write(f"- Mismatches: {len(mismatches)}\n\n")
        f.write(f"## Mismatch Details\n\n")
        for m in mismatches:
            f.write(f"### {m['name']}\n")
            f.write(f"- true_diffs: {m['true_diffs']}\n")
            f.write(f"- jump_diffs: {m['jump_diffs']}\n")
            if isinstance(m['details'], list):
                for d in m['details']:
                    f.write(f"  - {d}\n")
            else:
                f.write(f"- {m['details']}\n")
            f.write("\n")

    print(f"\nReport saved to {report_dir / 'baseline_report.md'}")

if __name__ == '__main__':
    main()
