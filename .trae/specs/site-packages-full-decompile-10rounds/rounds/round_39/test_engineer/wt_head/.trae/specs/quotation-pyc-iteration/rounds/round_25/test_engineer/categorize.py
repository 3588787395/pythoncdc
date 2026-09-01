"""R25 测试工程师：对20个失败函数进行精确分类，识别共性根因"""
import sys
import importlib.util
import dis
import types
from collections import Counter

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r23_decompiled.py'


def load_pyc_code_objects(pyc_path):
    from core.pyc_loader_v2 import load_pyc_file_v2
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


def get_instrs(co):
    return [(ins.offset, ins.opname, ins.argval, ins.argrepr)
            for ins in dis.get_instructions(co)
            if ins.opname not in ('EXTENDED_ARG', 'CACHE')]


def categorize(name, pyc_co, src_co):
    pi = get_instrs(pyc_co)
    si = get_instrs(src_co)
    diffs = []
    first_diff = None
    n = max(len(pi), len(si))
    for i in range(n):
        a = pi[i] if i < len(pi) else None
        b = si[i] if i < len(si) else None
        if not (a and b and a[1] == b[1] and a[2] == b[2]):
            if first_diff is None:
                first_diff = i
            diffs.append((i, a, b))

    if first_diff is None:
        return {'name': name, 'type': 'identical', 'first_diff': None}

    a = pi[first_diff] if first_diff < len(pi) else None
    b = si[first_diff] if first_diff < len(si) else None

    diff_type = 'unknown'
    detail = ''
    target_diff = None
    if a and b:
        if a[1] == b[1]:
            if 'JUMP' in a[1] or 'FOR_ITER' in a[1] or 'SETUP' in a[1]:
                diff_type = 'jump_target_diff'
                try:
                    if isinstance(a[2], int) and isinstance(b[2], int):
                        target_diff = b[2] - a[2]
                        detail = f"op={a[1]} p_tgt={a[2]} s_tgt={b[2]} diff={target_diff:+d}"
                    else:
                        detail = f"op={a[1]} p={a[2]!r} s={b[2]!r}"
                except Exception:
                    detail = f"op={a[1]} p={a[2]!r} s={b[2]!r}"
            else:
                diff_type = 'argval_diff'
                detail = f"op={a[1]} p={a[2]!r} s={b[2]!r}"
        else:
            diff_type = 'opname_diff'
            detail = f"p={a[1]}({a[3]}) s={b[1]}({b[3]})"
    elif a and not b:
        diff_type = 'src_missing_instr'
        detail = f"pyc has {a[1]}({a[3]}) but src ended (pyc_len={len(pi)}, src_len={len(si)})"
    elif b and not a:
        diff_type = 'src_extra_instr'
        detail = f"src has {b[1]}({b[3]}) but pyc ended (pyc_len={len(pi)}, src_len={len(si)})"

    # context around first diff
    start = max(0, first_diff - 3)
    end = min(n, first_diff + 6)
    ctx = []
    for i in range(start, end):
        a = pi[i] if i < len(pi) else None
        b = si[i] if i < len(si) else None
        mark = 'OK' if a and b and a[1] == b[1] and a[2] == b[2] else '!!'
        a_str = f"p:{a[0]:4d} {a[1]:30s} {a[3]}" if a else "p:(none)"
        b_str = f"s:{b[0]:4d} {b[1]:30s} {b[3]}" if b else "s:(none)"
        ctx.append(f"    [{i:3d}]{mark} {a_str}")
        ctx.append(f"         {mark} {b_str}")

    return {
        'name': name,
        'type': diff_type,
        'first_diff': first_diff,
        'detail': detail,
        'target_diff': target_diff,
        'pyc_len': len(pi),
        'src_len': len(si),
        'ctx': ctx,
    }


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    failures = [l.strip() for l in open('/tmp/r23_failures.txt') if l.strip()]

    print(f"=== R25 失败函数分类 (共 {len(failures)} 个) ===\n")
    results = []
    type_counter = Counter()
    diff_counter = Counter()

    for name in failures:
        if name not in pyc_codes or name not in src_codes:
            print(f"{name}: MISSING (pyc={name in pyc_codes}, src={name in src_codes})")
            continue
        r = categorize(name, pyc_codes[name], src_codes[name])
        results.append(r)
        type_counter[r['type']] += 1
        if r['target_diff'] is not None:
            diff_counter[r['target_diff']] += 1
        print(f"--- {name} (pyc={r['pyc_len']}, src={r['src_len']}, first_diff={r['first_diff']}) ---")
        print(f"  type: {r['type']}")
        print(f"  detail: {r['detail']}")
        for line in r['ctx']:
            print(line)
        print()

    print(f"\n=== 类型统计 ===")
    for t, c in type_counter.most_common():
        print(f"  {t}: {c}")

    print(f"\n=== 跳转目标偏移统计 ===")
    for d, c in diff_counter.most_common():
        print(f"  diff={d:+d}: {c}")

    # Group by type
    print(f"\n=== 按类型分组 ===")
    by_type = {}
    for r in results:
        by_type.setdefault(r['type'], []).append(r['name'])
    for t, names in by_type.items():
        print(f"  {t} ({len(names)}): {names}")


if __name__ == '__main__':
    main()
