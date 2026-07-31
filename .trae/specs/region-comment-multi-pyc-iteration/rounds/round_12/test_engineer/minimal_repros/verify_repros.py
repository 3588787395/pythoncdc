#!/usr/bin/env python3
"""R12 verify repros: compile → decompile → diff each minimal repro."""
import dis
import io
import marshal
import os
import py_compile
import sys
import types
from contextlib import redirect_stdout
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(PROJECT_ROOT))

from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode

REPRO_DIR = Path(__file__).resolve().parent


def extract_code_objects(code_obj):
    result = {}
    name = code_obj.co_name or '<module>'
    result[name] = code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const))
    return result


def verify_repro(py_path):
    """Compile py → pyc; decompile pyc → OK.py; compile OK.py; diff bytecode."""
    name = py_path.stem
    # Step 1: compile original
    pyc_path = py_path.with_suffix('.pyc')
    py_compile.compile(str(py_path), cfile=str(pyc_path), doraise=True)
    # Read orig code object
    with open(pyc_path, 'rb') as f:
        f.read(16)
        orig_code = marshal.load(f)

    # Step 2: decompile
    try:
        source = decompile_pyc(str(pyc_path))
    except Exception as e:
        return {'name': name, 'verdict': 'DECOMPILE-ERROR', 'error': f'{type(e).__name__}: {e}'}

    ok_path = py_path.with_suffix('.pyc.dec')
    with open(ok_path, 'w', encoding='utf-8') as f:
        f.write(source)

    # Step 3: compile decompiled
    ok_pyc_path = py_path.with_suffix('.OK.pyc')
    try:
        py_compile.compile(str(ok_path), cfile=str(ok_pyc_path), doraise=True)
    except Exception as e:
        return {'name': name, 'verdict': 'COMPILE-ERROR', 'error': f'{type(e).__name__}: {e}'}

    with open(ok_pyc_path, 'rb') as f:
        f.read(16)
        decomp_code = marshal.load(f)

    # Step 4: diff (compare all code objects by name)
    orig_map = extract_code_objects(orig_code)
    decomp_map = extract_code_objects(decomp_code)
    common = set(orig_map) & set(decomp_map)
    total = len(orig_map)
    matched = 0
    first_diff = None
    true_diffs_count = 0
    jump_diffs_count = 0
    mismatch_fn = None
    for fn_name in sorted(common):
        cmp = compare_bytecode(orig_map[fn_name], decomp_map[fn_name])
        if cmp.get('match'):
            matched += 1
        else:
            td = cmp.get('true_diffs', [])
            jd = cmp.get('jump_diffs', [])
            true_diffs_count += len(td)
            jump_diffs_count += len(jd)
            if first_diff is None and (td or jd):
                first_diff = (td or jd)[0]
                mismatch_fn = fn_name

    if matched == total:
        return {'name': name, 'verdict': 'NO-DEFECT', 'matched': matched, 'total': total}
    else:
        return {
            'name': name, 'verdict': 'DEFECT-REPRO', 'matched': matched, 'total': total,
            'true_diffs': true_diffs_count, 'jump_diffs': jump_diffs_count,
            'first_diff': first_diff, 'mismatch_fn': mismatch_fn,
        }


def main():
    repros = sorted(REPRO_DIR.glob('repro_*.py'))
    print(f'[R12-VERIFY] {len(repros)} repros')
    print('=' * 70)
    results = []
    for rp in repros:
        r = verify_repro(rp)
        results.append(r)
        if r['verdict'] == 'NO-DEFECT':
            print(f"  {r['name']}: NO-DEFECT ({r['matched']}/{r['total']})")
        elif r['verdict'] == 'DEFECT-REPRO':
            print(f"  {r['name']}: DEFECT-REPRO ({r['matched']}/{r['total']}) "
                  f"true_diffs={r['true_diffs']} jump_diffs={r['jump_diffs']} "
                  f"mismatch_fn={r['mismatch_fn']}")
            if r['first_diff']:
                print(f"      first_diff: {r['first_diff']}")
        else:
            print(f"  {r['name']}: {r['verdict']} {r.get('error','')}")

    defect = sum(1 for r in results if r['verdict'] == 'DEFECT-REPRO')
    nodefect = sum(1 for r in results if r['verdict'] == 'NO-DEFECT')
    error = sum(1 for r in results if r['verdict'] not in ('DEFECT-REPRO', 'NO-DEFECT'))
    print('=' * 70)
    print(f'[R12-VERIFY] DEFECT-REPRO={defect} NO-DEFECT={nodefect} ERROR={error}')


if __name__ == '__main__':
    main()
