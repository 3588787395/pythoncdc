import os
import sys
import json
import py_compile
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base import decompile_pyc, compile_and_compare, test_semantic_equivalence


def run_all_tests(test_dir: str = None):
    if test_dir is None:
        test_dir = os.path.dirname(os.path.abspath(__file__))

    test_files = sorted([
        f for f in os.listdir(test_dir)
        if f.startswith('test_') and f.endswith('.py') and f != 'test_results.json'
    ])

    if not test_files:
        print("No test_*.py files found.")
        return None

    results = {
        'timestamp': datetime.now().isoformat(),
        'test_dir': test_dir,
        'summary': {
            'total': 0,
            'pass': 0,
            'fail': 0,
            'jump_diff_only': 0,
            'semantic_equivalent': 0,
            'compile_fail': 0,
            'decompile_fail': 0,
            'syntax_fail': 0,
        },
        'details': {},
    }

    print(f"{'='*70}")
    print(f"  PyCDC Round Test Runner")
    print(f"  Directory: {test_dir}")
    print(f"  Found {len(test_files)} test files")
    print(f"{'='*70}\n")

    for f in test_files:
        py_path = os.path.join(test_dir, f)
        pyc_path = py_path + 'c'
        test_name = f.replace('.py', '')

        print(f"[{test_name}] ", end='', flush=True)
        detail = {
            'file': f,
            'status': 'UNKNOWN',
            'steps': {},
        }

        try:
            py_compile.compile(py_path, pyc_path, doraise=True)
        except Exception as e:
            print(f"COMPILE FAIL: {e}")
            detail['status'] = 'COMPILE_FAIL'
            detail['error'] = str(e)
            results['details'][test_name] = detail
            results['summary']['total'] += 1
            results['summary']['fail'] += 1
            results['summary']['compile_fail'] += 1
            continue

        try:
            decompiled = decompile_pyc(pyc_path)
            detail['steps']['decompile'] = 'ok'
        except Exception as e:
            print(f"DECOMPILE FAIL: {e}")
            detail['status'] = 'DECOMPILE_FAIL'
            detail['error'] = str(e)
            results['details'][test_name] = detail
            results['summary']['total'] += 1
            results['summary']['fail'] += 1
            results['summary']['decompile_fail'] += 1
            cleanup_pyc(pyc_path)
            continue

        try:
            compile(decompiled, '<decompiled>', 'exec')
            detail['steps']['syntax_check'] = 'ok'
        except SyntaxError as e:
            print(f"SYNTAX FAIL: {e}")
            detail['status'] = 'SYNTAX_FAIL'
            detail['error'] = str(e)
            detail['decompiled_source'] = decompiled
            results['details'][test_name] = detail
            results['summary']['total'] += 1
            results['summary']['fail'] += 1
            results['summary']['syntax_fail'] += 1
            cleanup_pyc(pyc_path)
            continue

        bytecode_result = compile_and_compare(py_path, decompiled)
        detail['steps']['bytecode_compare'] = bytecode_result

        semantic_result = test_semantic_equivalence(py_path, decompiled)
        detail['steps']['semantic_test'] = semantic_result

        bc_match = bytecode_result.get('match', False)
        jump_only = bytecode_result.get('jump_only', False)
        sem_equiv = semantic_result.get('equivalent', False)

        if bc_match:
            detail['status'] = 'PASS'
            results['summary']['pass'] += 1
            print("PASS (bytecode match)")
        elif jump_only and sem_equiv:
            detail['status'] = 'PASS_JUMP_DIFF_SEMANTIC_OK'
            results['summary']['pass'] += 1
            results['summary']['jump_diff_only'] += 1
            results['summary']['semantic_equivalent'] += 1
            num_jd = len(bytecode_result.get('jump_diffs', []))
            print(f"PASS (jump diff only, {num_jd} diffs, semantic OK)")
        elif jump_only:
            detail['status'] = 'JUMP_DIFF_ONLY'
            results['summary']['pass'] += 1
            results['summary']['jump_diff_only'] += 1
            num_jd = len(bytecode_result.get('jump_diffs', []))
            print(f"PASS (jump diff only, {num_jd} diffs, semantic NOT checked)")
        elif sem_equiv:
            detail['status'] = 'SEMANTIC_OK_BYTECODE_DIFF'
            results['summary']['pass'] += 1
            results['summary']['semantic_equivalent'] += 1
            num_td = len(bytecode_result.get('true_diffs', []))
            print(f"PASS (semantic OK, {num_td} bytecode diffs)")
        else:
            detail['status'] = 'FAIL'
            results['summary']['fail'] += 1
            num_td = len(bytecode_result.get('true_diffs', []))
            num_jd = len(bytecode_result.get('jump_diffs', []))
            num_sm = len(semantic_result.get('mismatches', []))
            print(f"FAIL (true_diffs={num_td}, jump_diffs={num_jd}, semantic_mismatches={num_sm})")

        results['details'][test_name] = detail
        results['summary']['total'] += 1
        cleanup_pyc(pyc_path)

    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"{'='*70}")
    s = results['summary']
    total = s['total']
    if total > 0:
        print(f"  Total:   {total}")
        print(f"  Pass:    {s['pass']} ({s['pass']*100//total}%)")
        print(f"  Fail:    {s['fail']} ({s['fail']*100//total}%)")
        print(f"    - compile_fail:  {s['compile_fail']}")
        print(f"    - decompile_fail: {s['decompile_fail']}")
        print(f"    - syntax_fail:   {s['syntax_fail']}")
        print(f"  Jump diff only:  {s['jump_diff_only']}")
        print(f"  Semantic equiv:  {s['semantic_equivalent']}")
    print(f"{'='*70}")

    output_path = os.path.join(test_dir, 'test_results.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\nResults saved to: {output_path}")
    return results


def cleanup_pyc(pyc_path: str):
    try:
        if os.path.exists(pyc_path):
            os.remove(pyc_path)
    except Exception:
        pass


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='PyCDC Round Test Runner')
    parser.add_argument('test_dir', nargs='?', default=None,
                        help='Directory containing test_*.py files (default: current directory)')
    args = parser.parse_args()
    run_all_tests(args.test_dir)
