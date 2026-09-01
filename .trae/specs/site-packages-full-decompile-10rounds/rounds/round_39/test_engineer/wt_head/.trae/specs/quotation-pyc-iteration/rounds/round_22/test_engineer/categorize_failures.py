"""R22 测试工程师：分类40个失败函数的首次差异模式"""
import sys
import dis
import types
from collections import Counter

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r22_decompiled.py'


def load_pyc_code_objects(pyc_path):
    module = load_pyc_file_v2(pyc_path)
    if not module:
        return {}
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    result = {}
    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        result[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)
    walk(code_obj)
    return result


def load_src_code_objects(src_path):
    with open(src_path, 'r', encoding='utf-8') as f:
        src = f.read()
    code_obj = compile(src, '<decompiled>', 'exec')
    result = {}
    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        result[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)
    walk(code_obj)
    return result


def get_instr_list(co):
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    with open('/tmp/r22_failures.txt') as f:
        failures = [l.strip() for l in f if l.strip()]

    categories = Counter()
    details = []

    for name in failures:
        if name not in pyc_codes or name not in src_codes:
            categories['missing'] += 1
            continue
        pc = pyc_codes[name]
        sc = src_codes[name]
        pi = get_instr_list(pc)
        si = get_instr_list(sc)
        len_diff = len(pi) - len(si)

        # find first diff
        min_len = min(len(pi), len(si))
        first_diff_idx = None
        first_diff_kind = None
        for i in range(min_len):
            a = pi[i]
            b = si[i]
            if a[1] != b[1]:
                first_diff_idx = i
                first_diff_kind = f'opname: {a[1]} != {b[1]}'
                break
            if a[2] != b[2]:
                if isinstance(a[2], types.CodeType) or isinstance(b[2], types.CodeType):
                    first_diff_idx = i
                    first_diff_kind = 'code_obj'
                    break
                # Check if it's a jump target diff
                if 'JUMP' in a[1] or 'POP_JUMP' in a[1] or 'FOR_ITER' in a[1]:
                    first_diff_idx = i
                    first_diff_kind = f'jump_target: {a[2]} != {b[2]} (op={a[1]})'
                    break
                else:
                    first_diff_idx = i
                    first_diff_kind = f'argval: {a[2]!r} != {b[2]!r} (op={a[1]})'
                    break
        if first_diff_idx is None and len_diff != 0:
            first_diff_idx = min_len
            first_diff_kind = f'len_only: pyc={len(pi)} src={len(si)}'

        cat = first_diff_kind.split(':')[0] if first_diff_kind else 'unknown'
        categories[cat] += 1
        details.append((name, len(pi), len(si), first_diff_idx, first_diff_kind))

    print("=== 失败模式分类 ===")
    for cat, cnt in categories.most_common():
        print(f"  {cnt:3d}  {cat}")

    print(f"\n=== 详情（按类别分组）===")
    # Group by category
    from itertools import groupby
    details_sorted = sorted(details, key=lambda x: x[4].split(':')[0] if x[4] else 'unknown')
    for cat, group in groupby(details_sorted, key=lambda x: x[4].split(':')[0] if x[4] else 'unknown'):
        print(f"\n--- {cat} ---")
        for name, plen, slen, idx, kind in group:
            print(f"  {name}: pyc={plen} src={slen} diff@{idx} {kind}")


if __name__ == '__main__':
    main()
