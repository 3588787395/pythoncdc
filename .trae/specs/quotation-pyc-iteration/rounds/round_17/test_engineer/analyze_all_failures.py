"""R17 测试工程师：分析所有失败函数的差异模式"""
import sys
import importlib.util
import dis
import types
from collections import Counter

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r17_decompiled.py'


def load_pyc_code_objects(pyc_path):
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(pyc_path)
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
        if ins.opname == 'EXTENDED_ARG':
            continue
        if ins.opname == 'CACHE':
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    with open('/tmp/r17_failures.txt') as f:
        failures = [l.strip() for l in f if l.strip()]

    print(f"=== 失败函数差异模式分析 ({len(failures)} 个) ===\n")

    patterns = Counter()
    detail = []

    for name in failures:
        pc = pyc_codes.get(name)
        sc = src_codes.get(name)
        if not pc or not sc:
            patterns['missing'] += 1
            detail.append((name, 'missing', None, None, None))
            continue

        p = get_instr_list(pc)
        s = get_instr_list(sc)
        delta = len(s) - len(p)

        # 找出第一个差异
        first_diff = None
        for i, (pi, si) in enumerate(zip(p, s)):
            if pi != si:
                first_diff = (i, pi, si)
                break

        if delta != 0:
            key = f'length_diff(delta={delta})'
            patterns[key] += 1
            detail.append((name, key, first_diff, p, s))
        elif first_diff:
            idx, pi, si = first_diff
            p_off, p_op, p_arg = pi
            s_off, s_op, s_arg = si
            if p_op != s_op:
                key = f'opname_diff:{p_op}_vs_{s_op}'
                patterns[key] += 1
                detail.append((name, key, first_diff, p, s))
            elif p_arg != s_arg:
                if 'JUMP' in p_op or 'POP_JUMP' in p_op or 'FOR_ITER' in p_op or 'SETUP' in p_op:
                    key = f'jump_target_diff:{p_op}'
                    patterns[key] += 1
                    detail.append((name, key, first_diff, p, s))
                elif p_op in ('LOAD_CONST',):
                    key = f'const_diff:{p_op}'
                    patterns[key] += 1
                    detail.append((name, key, first_diff, p, s))
                elif p_op in ('LOAD_FAST', 'STORE_FAST', 'LOAD_GLOBAL', 'STORE_GLOBAL',
                              'LOAD_DEREF', 'STORE_DEREF', 'LOAD_NAME', 'STORE_NAME'):
                    key = f'name_diff:{p_op}'
                    patterns[key] += 1
                    detail.append((name, key, first_diff, p, s))
                else:
                    key = f'argval_diff:{p_op}'
                    patterns[key] += 1
                    detail.append((name, key, first_diff, p, s))
        else:
            # 长度相同内容相同 - 不会到这里
            patterns['unknown'] += 1
            detail.append((name, 'unknown', None, p, s))

    print("=== 失败模式分布 ===")
    for pat, cnt in patterns.most_common():
        print(f"  {cnt:3d}  {pat}")

    # 输出前3个失败函数的详细 diff
    print(f"\n=== 失败函数详细 diff (前 5 个 length_diff) ===")
    for name, key, first_diff, p, s in detail:
        if 'length_diff' in key:
            print(f"\n--- {name} ({key}) ---")
            print(f"  pyc len={len(p)}, src len={len(s)}, delta={len(s)-len(p)}")
            if first_diff:
                idx, pi, si = first_diff
                lo = max(0, idx - 3)
                hi = min(len(p), idx + 5)
                print(f"  first diff at idx={idx}:")
                print(f"    pyc: {pi}")
                print(f"    src: {si}")
                print(f"  context (pyc):")
                for i in range(lo, hi):
                    marker = '>>' if i == idx else '  '
                    if i < len(p):
                        print(f"    {marker} [{i}] {p[i]}")
                print(f"  context (src):")
                for i in range(lo, hi):
                    marker = '>>' if i == idx else '  '
                    if i < len(s):
                        print(f"    {marker} [{i}] {s[i]}")
            break  # 只输出第一个

    # 输出每种模式的代表函数
    print(f"\n=== 每种模式的代表函数 ===")
    seen_pats = set()
    for name, key, first_diff, p, s in detail:
        if key in seen_pats:
            continue
        seen_pats.add(key)
        print(f"\n--- [{key}] {name} ---")
        if first_diff:
            idx, pi, si = first_diff
            print(f"  first diff at idx={idx}: pyc={pi} vs src={si}")
            lo = max(0, idx - 2)
            hi = min(len(p), idx + 4)
            print(f"  pyc[{lo}:{hi}]:")
            for i in range(lo, hi):
                if i < len(p):
                    marker = '>>' if i == idx else '  '
                    print(f"    {marker} [{i}] {p[i]}")
            print(f"  src[{lo}:{hi}]:")
            for i in range(lo, hi):
                if i < len(s):
                    marker = '>>' if i == idx else '  '
                    print(f"    {marker} [{i}] {s[i]}")


if __name__ == '__main__':
    main()
