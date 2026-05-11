import os
import sys
import json
import marshal
import types
import dis
import re
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
PYCDC_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, PYCDC_ROOT)

from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode, get_bytecode_instructions

PYC_PATH = os.path.join(PYCDC_ROOT, 'quotation.pyc')
REPORT_PATH = os.path.join(HERE, 'quotation_bc_report.json')


def fix_syntax_errors(source):
    fixed = source
    changed = True
    iterations = 0
    while changed and iterations < 50:
        changed = False
        iterations += 1
        try:
            compile(fixed, '<decompiled>', 'exec')
            break
        except SyntaxError as e:
            lineno = e.lineno
            msg = str(e)
            if lineno is None:
                break
            lines = fixed.split('\n')
            if lineno < 1 or lineno > len(lines):
                break
            idx = lineno - 1
            error_line = lines[idx] if idx < len(lines) else ''
            prev_line = lines[idx - 1] if idx > 0 else ''
            prev_stripped = prev_line.rstrip()
            indent_match = re.match(r'^(\s*)', prev_stripped)
            base_indent = indent_match.group(1) if indent_match else ''

            if 'expected an indented block' in msg:
                colon_endings = (':', ':\\', ': #')
                if prev_stripped.endswith(':'):
                    insert_indent = base_indent + '    '
                    lines.insert(idx, insert_indent + 'pass')
                    fixed = '\n'.join(lines)
                    changed = True
                else:
                    break
            elif 'unexpected indent' in msg:
                break
            elif "expected ':'" in msg:
                break
            else:
                break
    return fixed


def extract_code_objects(code_obj, prefix=''):
    results = []
    name = prefix + code_obj.co_name if prefix else code_obj.co_name
    if name == '<module>':
        name = '<module>'
    results.append((name, code_obj))
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            sub_prefix = name + '.' if name != '<module>' else ''
            results.extend(extract_code_objects(const, sub_prefix))
    return results


def classify_diff_pattern(orig_instr, decomp_instr, diff_type, context_instrs=None):
    if diff_type == 'extra_in_decomp':
        op = decomp_instr.get('decomp_op', '') if isinstance(decomp_instr, dict) else ''
        if op == 'RETURN_VALUE' or op == 'LOAD_CONST':
            return 'return_none'
        if op == 'NOP':
            return 'pass_stmt'
        return 'other'
    if diff_type == 'missing_in_decomp':
        op = orig_instr.get('orig_op', '') if isinstance(orig_instr, dict) else ''
        if op == 'RETURN_VALUE' or op == 'LOAD_CONST':
            return 'return_none'
        if op == 'NOP':
            return 'pass_stmt'
        return 'other'

    orig_op = orig_instr.get('orig_op', '') if isinstance(orig_instr, dict) else ''
    decomp_op = decomp_instr.get('decomp_op', '') if isinstance(decomp_instr, dict) else ''
    orig_arg = orig_instr.get('orig_arg', '')
    decomp_arg = decomp_instr.get('decomp_arg', '')

    jump_ops = {
        'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
        'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
        'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
        'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
        'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP',
        'FOR_ITER', 'SEND', 'SETUP_FINALLY', 'SETUP_WITH',
    }

    both_jump = orig_op in jump_ops and decomp_op in jump_ops
    one_jump = orig_op in jump_ops or decomp_op in jump_ops

    if one_jump or both_jump:
        if 'FOR_ITER' in (orig_op, decomp_op):
            return 'for_loop'
        if 'SETUP_WITH' in (orig_op, decomp_op):
            return 'with_statement'
        if 'SETUP_FINALLY' in (orig_op, decomp_op):
            return 'try_except'
        if context_instrs:
            for ci in context_instrs:
                ci_op = ci.opname if hasattr(ci, 'opname') else ''
                if ci_op == 'SETUP_FINALLY':
                    return 'try_except'
                if ci_op == 'SETUP_WITH':
                    return 'with_statement'
                if ci_op == 'FOR_ITER':
                    return 'for_loop'
        if orig_op.startswith('POP_JUMP') or decomp_op.startswith('POP_JUMP'):
            return 'if_else'
        if orig_op.startswith('JUMP') or decomp_op.startswith('JUMP'):
            return 'while_break'
        return 'other'

    if orig_op.startswith('COMPARE_') or decomp_op.startswith('COMPARE_'):
        return 'chained_compare'
    if orig_op in ('CONTAINS_OP', 'IS_OP') or decomp_op in ('CONTAINS_OP', 'IS_OP'):
        return 'chained_compare'

    bool_ops = {'AND', 'OR', 'NOT', 'UNARY_NOT'}
    if any(x in orig_op for x in bool_ops) or any(x in decomp_op for x in bool_ops):
        return 'bool_op'

    if orig_op == 'LOAD_CONST' and decomp_op == 'LOAD_CONST':
        if orig_arg is None and decomp_arg is not None:
            return 'return_none'
        if decomp_arg is None and orig_arg is not None:
            return 'return_none'

    if orig_op == 'NOP' or decomp_op == 'NOP':
        return 'pass_stmt'

    if orig_op == 'RETURN_VALUE' or decomp_op == 'RETURN_VALUE':
        return 'return_none'

    if orig_op != decomp_op:
        if 'CALL' in orig_op or 'CALL' in decomp_op:
            return 'ternary'
        return 'other'

    return 'other'


def find_decomp_code_by_name(decomp_code, target_name):
    if decomp_code.co_name == target_name:
        return decomp_code
    for const in decomp_code.co_consts:
        if isinstance(const, types.CodeType):
            result = find_decomp_code_by_name(const, target_name)
            if result is not None:
                return result
    return None


def find_decomp_code_by_path(decomp_code, name_path):
    parts = name_path.split('.')
    current = decomp_code
    for part in parts:
        if current.co_name == part:
            continue
        found = False
        for const in current.co_consts:
            if isinstance(const, types.CodeType) and const.co_name == part:
                current = const
                found = True
                break
        if not found:
            for const in current.co_consts:
                if isinstance(const, types.CodeType):
                    result = find_decomp_code_by_name(const, part)
                    if result is not None:
                        current = result
                        found = True
                        break
        if not found:
            return None
    return current


def main():
    print(f"PYC file: {PYC_PATH}")
    print(f"Report output: {REPORT_PATH}")
    print()

    print("Step 1: Decompiling quotation.pyc ...")
    try:
        decompiled_source = decompile_pyc(PYC_PATH)
        print(f"  Decompilation succeeded, source length: {len(decompiled_source)} chars")
    except Exception as e:
        print(f"  Decompilation FAILED: {e}")
        report = {
            'summary': {'total': 0, 'match': 0, 'mismatch': 0, 'error': 1},
            'results': [],
            'error': str(e),
        }
        with open(REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        return

    print()
    print("Step 2: Loading original pyc and extracting code objects ...")
    with open(PYC_PATH, 'rb') as f:
        magic = f.read(4)
        flags = int.from_bytes(f.read(4), 'little')
        if flags & 0x1:
            f.read(8)
        else:
            f.read(8)
        code_obj = marshal.load(f)

    orig_codes = extract_code_objects(code_obj)
    print(f"  Found {len(orig_codes)} code objects in original pyc")

    print()
    print("Step 3: Compiling decompiled source ...")
    try:
        decomp_code = compile(decompiled_source, '<decompiled>', 'exec')
        print("  Compilation succeeded")
    except SyntaxError as e:
        print(f"  Initial compilation FAILED (SyntaxError): {e}")
        print("  Attempting to fix syntax errors ...")
        fixed_source = fix_syntax_errors(decompiled_source)
        try:
            decomp_code = compile(fixed_source, '<decompiled>', 'exec')
            print("  Fixed compilation succeeded")
            decompiled_source = fixed_source
        except SyntaxError as e2:
            print(f"  Fix FAILED too (SyntaxError): {e2}")
            report = {
                'summary': {'total': len(orig_codes), 'match': 0, 'mismatch': 0, 'error': len(orig_codes)},
                'results': [{'name': name, 'status': 'ERROR', 'error': f'SyntaxError in decompiled source: {e2}'} for name, _ in orig_codes],
            }
            with open(REPORT_PATH, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            return

    decomp_codes = extract_code_objects(decomp_code)
    decomp_name_map = {}
    for name, co in decomp_codes:
        decomp_name_map[name] = co

    print()
    print("Step 4: Comparing bytecode for each function ...")

    results = []
    match_count = 0
    mismatch_count = 0
    error_count = 0

    for orig_name, orig_co in orig_codes:
        entry = {
            'name': orig_name,
            'status': 'UNKNOWN',
            'orig_count': 0,
            'decomp_count': 0,
            'jump_diffs': 0,
            'true_diffs': 0,
            'diff_categories': [],
        }

        decomp_co = decomp_name_map.get(orig_name)
        if decomp_co is None:
            for dname, dco in decomp_codes:
                if dname.endswith('.' + orig_co.co_name) or dname == orig_co.co_name:
                    decomp_co = dco
                    break

        if decomp_co is None:
            entry['status'] = 'MISSING'
            entry['orig_count'] = len(get_bytecode_instructions(orig_co))
            mismatch_count += 1
            results.append(entry)
            continue

        try:
            cmp_result = compare_bytecode(orig_co, decomp_co)
            entry['orig_count'] = cmp_result['orig_count']
            entry['decomp_count'] = cmp_result['decomp_count']
            entry['jump_diffs'] = len(cmp_result.get('jump_diffs', []))
            entry['true_diffs'] = len(cmp_result.get('true_diffs', []))

            all_diffs = cmp_result.get('jump_diffs', []) + cmp_result.get('true_diffs', [])
            categories = set()
            for diff in all_diffs:
                diff_type = diff.get('type', '')
                cat = classify_diff_pattern(diff, diff, diff_type)
                categories.add(cat)
            entry['diff_categories'] = sorted(categories)

            if cmp_result['match']:
                entry['status'] = 'MATCH'
                match_count += 1
            elif cmp_result.get('jump_only'):
                entry['status'] = 'JUMP_ONLY_DIFF'
                mismatch_count += 1
            else:
                entry['status'] = 'TRUE_DIFF'
                mismatch_count += 1

        except Exception as e:
            entry['status'] = 'ERROR'
            entry['error'] = str(e)
            error_count += 1

        results.append(entry)

    total = len(orig_codes)
    summary = {
        'total': total,
        'match': match_count,
        'mismatch': mismatch_count,
        'error': error_count,
    }

    report = {
        'summary': summary,
        'results': results,
    }

    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 60)
    print("QUOTATION BYTECODE COMPARISON REPORT")
    print("=" * 60)
    print(f"  Total functions:  {total}")
    print(f"  MATCH:            {match_count}")
    print(f"  MISMATCH:         {mismatch_count}")
    print(f"  ERROR:            {error_count}")
    if total > 0:
        print(f"  Match rate:       {match_count}/{total} = {match_count*100/total:.1f}%")
    print()

    status_counts = {}
    for r in results:
        s = r['status']
        status_counts[s] = status_counts.get(s, 0) + 1
    print("  Status breakdown:")
    for s, c in sorted(status_counts.items()):
        print(f"    {s}: {c}")

    all_cats = set()
    for r in results:
        if r.get('diff_categories'):
            all_cats.update(r['diff_categories'])
    if all_cats:
        print()
        print("  Diff categories found:")
        cat_counts = {}
        for r in results:
            for cat in r.get('diff_categories', []):
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
        for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
            print(f"    {cat}: {cnt}")

    non_match = [r for r in results if r['status'] not in ('MATCH',)]
    if non_match:
        print()
        print("  Non-matching functions:")
        for r in non_match:
            cats = ', '.join(r.get('diff_categories', []))
            print(f"    {r['name']}: {r['status']} (orig={r['orig_count']}, decomp={r['decomp_count']}, jump_diffs={r['jump_diffs']}, true_diffs={r['true_diffs']}) [{cats}]")

    print()
    print(f"Report saved to: {REPORT_PATH}")


if __name__ == '__main__':
    main()
