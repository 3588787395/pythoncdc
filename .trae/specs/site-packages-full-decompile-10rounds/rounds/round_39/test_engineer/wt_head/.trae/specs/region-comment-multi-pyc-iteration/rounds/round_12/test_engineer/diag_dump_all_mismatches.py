#!/usr/bin/env python3
"""R12 diagnostic: dump all 21 mismatches of klinedata.pyc + dis.dis for each.

Identify Pattern A2 candidates (try-body if with simple condition + multi-branch return).
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

# file: .trae/specs/.../rounds/round_12/test_engineer/diag_dump_all_mismatches.py
# 7 parents up to project root (f:\Downloads\pythoncdc-main)
PROJECT_ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(PROJECT_ROOT))

from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode


def load_pyc_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def extract_code_objects(code_obj):
    result = {}
    name = code_obj.co_name or '<module>'
    result[name] = code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const))
    return result


def dis_str(code_obj):
    buf = io.StringIO()
    with redirect_stdout(buf):
        dis.dis(code_obj)
    return buf.getvalue()


def main():
    pyc_path = str(PROJECT_ROOT / 'site-packages/IQCommon/api/klinedata.pyc')
    ok_py_path = str(PROJECT_ROOT / 'site-packages/IQCommon/api/klinedataOK.py')

    print(f'[R12-DIAG] pyc={pyc_path}')
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
    for name in sorted(common):
        cmp = compare_bytecode(orig_map[name], decomp_map[name])
        if not cmp.get('match'):
            mismatches.append({
                'name': name,
                'orig_count': cmp.get('orig_count', 0),
                'decomp_count': cmp.get('decomp_count', 0),
                'jump_diffs': len(cmp.get('jump_diffs', [])),
                'true_diffs': len(cmp.get('true_diffs', [])),
                'first_diff': (cmp.get('true_diffs') or cmp.get('jump_diffs'))[0] if (cmp.get('true_diffs') or cmp.get('jump_diffs')) else None,
            })

    print(f'\n[R12-DIAG] total={len(orig_map)} matched={len(orig_map)-len(mismatches)} mismatches={len(mismatches)}')
    print('=' * 70)
    print('ALL MISMATCHES:')
    for m in mismatches:
        print(f"  - {m['name']}: orig={m['orig_count']} decomp={m['decomp_count']} "
              f"jump_diffs={m['jump_diffs']} true_diffs={m['true_diffs']}")
        if m['first_diff']:
            print(f"      first_diff: {m['first_diff']}")

    # Save full dis for all mismatches
    out_dir = PROJECT_ROOT / '.trae/specs/region-comment-multi-pyc-iteration/rounds/round_12/test_engineer'
    for m in mismatches:
        name = m['name']
        safe = name.replace('<', '').replace('>', '').replace(':', '_')
        with open(out_dir / f'_dis_{safe}_orig.txt', 'w', encoding='utf-8') as f:
            f.write(f'# ORIG dis.dis({name})\n')
            f.write(dis_str(orig_map[name]))
        with open(out_dir / f'_dis_{safe}_decomp.txt', 'w', encoding='utf-8') as f:
            f.write(f'# DECOMP dis.dis({name})\n')
            f.write(dis_str(decomp_map[name]))

    print(f'\n[R12-DIAG] dis dumps saved to {out_dir}/_dis_*_{{orig,decomp}}.txt')


if __name__ == '__main__':
    main()
