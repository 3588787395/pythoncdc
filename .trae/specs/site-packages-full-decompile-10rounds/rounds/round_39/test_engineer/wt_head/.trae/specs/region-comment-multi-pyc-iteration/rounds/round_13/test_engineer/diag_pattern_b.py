#!/usr/bin/env python3
"""R13 diagnostic: identify and characterize Pattern B (scope) in klinedata.pyc.

For each mismatched function:
  - dump first N true_diffs (skip jump-arg-only diffs)
  - categorize sub-pattern (B1=LOAD_GLOBAL->LOAD_FAST, B2=LOAD_FAST->LOAD_GLOBAL,
    B3=name mismatch, B4=STORE_FAST vs STORE_NAME)
"""
import dis
import io
import marshal
import os
import py_compile
import sys
import types
from contextlib import redirect_stdout
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(PROJECT_ROOT))

from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode, _normalize_argval


def load_pyc_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def extract_code_objects(code_obj, out=None):
    if out is None:
        out = {}
    name = code_obj.co_name or '<module>'
    out[name] = code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            extract_code_objects(const, out)
    return out


def categorize_first_true_diff(orig_code, decomp_code):
    """Return (sub_pattern, descriptor) for the first true diff."""
    cmp = compare_bytecode(orig_code, decomp_code)
    if cmp.get('match'):
        return ('MATCH', cmp)
    td = cmp.get('true_diffs') or []
    jd = cmp.get('jump_diffs') or []
    if not td:
        return ('JUMP_ONLY', cmp)
    d = td[0]
    oo = d.get('orig_op'); do = d.get('decomp_op')
    oa = d.get('orig_arg'); da = d.get('decomp_arg')
    # Classify
    if oo == do:
        # Same opcode, different arg (name mismatch / scope swap with same opcode)
        if oo in ('LOAD_FAST', 'LOAD_GLOBAL'):
            return ('B3_NAME_MISMATCH', d)
        if oo in ('STORE_FAST', 'STORE_NAME'):
            return ('B4_STORE_SCOPE', d)
        return ('ARG_MISMATCH', d)
    # Different opcode
    if oo == 'LOAD_GLOBAL' and do == 'LOAD_FAST':
        return ('B1_GLOBAL_TO_FAST', d)
    if oo == 'LOAD_FAST' and do == 'LOAD_GLOBAL':
        return ('B2_FAST_TO_GLOBAL', d)
    if oo == 'STORE_FAST' and do == 'STORE_NAME':
        return ('B4_STORE_SCOPE', d)
    if oo == 'STORE_NAME' and do == 'STORE_FAST':
        return ('B4_STORE_SCOPE', d)
    if do == 'NOP':
        return ('R_NOP_PADDING', d)
    if oo == 'NOP':
        return ('R_NOP_MISSING', d)
    if 'EXTENDED_ARG' in (oo, do):
        return ('E_JUMP_RENUMBER', d)
    if 'POP_JUMP' in (oo, do):
        return ('E_POP_JUMP_DIFF', d)
    if 'SWAP' in (oo, do) or 'POP_TOP' in (oo, do):
        return ('C_SWAP_POP', d)
    if 'UNPACK_SEQUENCE' in (oo, do):
        return ('C2_UNPACK', d)
    return ('OTHER', d)


def main():
    pyc_path = str(PROJECT_ROOT / 'site-packages/IQCommon/api/klinedata.pyc')
    ok_py_path = str(PROJECT_ROOT / 'site-packages/IQCommon/api/klinedataOK.py')

    print(f'[R13-DIAG] pyc={pyc_path}')
    source = decompile_pyc(pyc_path)
    with open(ok_py_path, 'w', encoding='utf-8') as f:
        f.write(source)

    orig_code = load_pyc_code(pyc_path)
    orig_map = extract_code_objects(orig_code)

    cfile = py_compile.compile(ok_py_path, doraise=True, quiet=2)
    with open(cfile, 'rb') as f:
        f.read(16)
        decomp_code = marshal.load(f)
    decomp_map = extract_code_objects(decomp_code)

    common = set(orig_map) & set(decomp_map)
    mismatches = []
    pattern_counts = {}
    for name in sorted(common):
        cmp = compare_bytecode(orig_map[name], decomp_map[name])
        if not cmp.get('match'):
            sub, desc = categorize_first_true_diff(orig_map[name], decomp_map[name])
            mismatches.append({
                'name': name,
                'sub': sub,
                'desc': desc,
                'orig_count': cmp.get('orig_count', 0),
                'decomp_count': cmp.get('decomp_count', 0),
                'jump_diffs': len(cmp.get('jump_diffs', [])),
                'true_diffs': len(cmp.get('true_diffs', [])),
                'cmp': cmp,
            })
            pattern_counts[sub] = pattern_counts.get(sub, 0) + 1

    print(f'\n[R13-DIAG] total={len(orig_map)} matched={len(orig_map)-len(mismatches)} mismatches={len(mismatches)}')
    print('=' * 70)
    print('PATTERN COUNTS (by first true_diff):')
    for sub, cnt in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        print(f'  {sub:30s} {cnt}')
    print('=' * 70)
    print('ALL MISMATCHES:')
    for m in mismatches:
        d = m['desc'] if isinstance(m['desc'], dict) else {}
        print(f"  - {m['name']:40s} sub={m['sub']:20s} td={m['true_diffs']:3d} jd={m['jump_diffs']:3d}")
        if isinstance(d, dict):
            print(f"      first_true_diff: idx={d.get('index')} orig={d.get('orig_op')}({d.get('orig_arg')!r}) decomp={d.get('decomp_op')}({d.get('decomp_arg')!r})")
    # Save full first 30 true_diffs per mismatch
    out_dir = PROJECT_ROOT / '.trae/specs/region-comment-multi-pyc-iteration/rounds/round_13/test_engineer'
    with open(out_dir / '_all_mismatches_summary.txt', 'w', encoding='utf-8') as f:
        f.write(f'total={len(orig_map)} matched={len(orig_map)-len(mismatches)} mismatches={len(mismatches)}\n\n')
        f.write('PATTERN COUNTS:\n')
        for sub, cnt in sorted(pattern_counts.items(), key=lambda x: -x[1]):
            f.write(f'  {sub:30s} {cnt}\n')
        f.write('\n' + '=' * 80 + '\n')
        for m in mismatches:
            f.write(f"\n=== {m['name']} (sub={m['sub']}, td={m['true_diffs']}, jd={m['jump_diffs']}) ===\n")
            cmp = m['cmp']
            for i, d in enumerate(cmp.get('true_diffs', [])[:30]):
                f.write(f"  [{i}] idx={d.get('index')} orig={d.get('orig_op')}({d.get('orig_arg')!r}) decomp={d.get('decomp_op')}({d.get('decomp_arg')!r}) type={d.get('type','')}\n")
            f.write('  --- first 15 jump_diffs ---\n')
            for i, d in enumerate(cmp.get('jump_diffs', [])[:15]):
                f.write(f"  [j{i}] idx={d.get('index')} orig={d.get('orig_op')}({d.get('orig_arg')!r}) decomp={d.get('decomp_op')}({d.get('decomp_arg')!r})\n")
    print(f"\n[R13-DIAG] summary saved to {out_dir}/_all_mismatches_summary.txt")


if __name__ == '__main__':
    main()
