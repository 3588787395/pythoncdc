import sys
import os
import types
import marshal
import dis
import importlib.util
import py_compile
import json

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', '..'))
sys.path.insert(0, _project_root)
sys.path.insert(0, os.path.join(_project_root, 'testqouter', 'round1'))

from base import compare_bytecode, _filter_noise_instrs, _normalize_argval

PYC_PATH = r'F:\Downloads\pythoncdc-main\site-packages\IQCommon\api\klinedata.pyc'
OK_PATH = r'F:\Downloads\pythoncdc-main\site-packages\IQCommon\api\klinedataOK.py'
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_all_codes(code, prefix=''):
    result = {}
    name = prefix + code.co_name
    result[name] = code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(get_all_codes(const, name + '.'))
    return result


def load_pyc_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        magic = f.read(4)
        flags = int.from_bytes(f.read(4), 'little')
        if flags & 0x1:
            f.read(8)
        else:
            f.read(8)
        return marshal.load(f)


def load_py_code(py_path):
    with open(py_path, 'r', encoding='utf-8') as f:
        source = f.read()
    return compile(source, py_path, 'exec')


def classify_diff(diff):
    if diff.get('type') == 'extra_in_decomp':
        return 'extra_instruction'
    if diff.get('type') == 'missing_in_decomp':
        return 'missing_instruction'
    orig_op = diff.get('orig_op', '')
    decomp_op = diff.get('decomp_op', '')
    if orig_op and decomp_op and orig_op != decomp_op:
        return 'different_opcode'
    if orig_op and decomp_op and orig_op == decomp_op:
        return 'different_argument'
    return 'unknown'


def main():
    print("Loading original pyc...")
    orig_code = load_pyc_code(PYC_PATH)
    orig_funcs = get_all_codes(orig_code)
    print(f"Original: {len(orig_funcs)} code objects")

    print("Compiling OK.py...")
    try:
        py_compile.compile(OK_PATH, doraise=True)
        print("OK.py compiles successfully")
    except SyntaxError as e:
        print(f"SyntaxError in OK.py: {e}")
        return

    print("Loading compiled OK.py...")
    decomp_code = load_py_code(OK_PATH)
    decomp_funcs = get_all_codes(decomp_code)
    print(f"Decompiled: {len(decomp_funcs)} code objects")

    matched = 0
    mismatched = []
    jump_only = 0
    all_results = {}

    for name in sorted(orig_funcs.keys()):
        if name not in decomp_funcs:
            mismatched.append({
                'function': name,
                'issue': 'missing_in_decomp',
                'first_diff_offset': 0,
                'diff_type': 'missing_function',
                'diffs': []
            })
            continue

        result = compare_bytecode(orig_funcs[name], decomp_funcs[name])
        all_results[name] = result

        if result['match']:
            matched += 1
            if result.get('jump_only'):
                jump_only += 1
        else:
            true_diffs = result.get('true_diffs', [])
            first_offset = true_diffs[0]['index'] if true_diffs else -1
            diff_categories = {}
            for d in true_diffs:
                cat = classify_diff(d)
                diff_categories[cat] = diff_categories.get(cat, 0) + 1

            mismatched.append({
                'function': name,
                'issue': 'bytecode_mismatch',
                'first_diff_offset': first_offset,
                'diff_type': max(diff_categories, key=diff_categories.get) if diff_categories else 'unknown',
                'diff_categories': diff_categories,
                'num_true_diffs': len(true_diffs),
                'num_jump_diffs': len(result.get('jump_diffs', [])),
                'orig_count': result.get('orig_count', 0),
                'decomp_count': result.get('decomp_count', 0),
                'first_5_diffs': true_diffs[:5]
            })

    total = len(orig_funcs)
    rate = matched / total if total > 0 else 0

    print(f"\n=== RESULTS ===")
    print(f"Matched: {matched}/{total} ({rate:.2%})")
    print(f"Jump-only matches: {jump_only}")
    print(f"Mismatched: {len(mismatched)}")

    for m in mismatched:
        print(f"\n  Function: {m['function']}")
        print(f"  First diff at index: {m['first_diff_offset']}")
        print(f"  Diff type: {m['diff_type']}")
        print(f"  Categories: {m.get('diff_categories', {})}")
        print(f"  True diffs: {m.get('num_true_diffs', 0)}, Jump diffs: {m.get('num_jump_diffs', 0)}")
        print(f"  Orig instrs: {m.get('orig_count', 0)}, Decomp instrs: {m.get('decomp_count', 0)}")
        for d in m.get('first_5_diffs', []):
            print(f"    @{d['index']}: orig={d.get('orig_op','?')}({d.get('orig_arg','')}) decomp={d.get('decomp_op','?')}({d.get('decomp_arg','')})")

    with open(os.path.join(OUT_DIR, 'bytecode_results.json'), 'w', encoding='utf-8') as f:
        json.dump({
            'matched': matched,
            'total': total,
            'rate': rate,
            'jump_only': jump_only,
            'mismatched': mismatched
        }, f, indent=2, ensure_ascii=False, default=str)

    print(f"\nResults saved to bytecode_results.json")
    return matched, total, rate, mismatched


if __name__ == '__main__':
    main()
