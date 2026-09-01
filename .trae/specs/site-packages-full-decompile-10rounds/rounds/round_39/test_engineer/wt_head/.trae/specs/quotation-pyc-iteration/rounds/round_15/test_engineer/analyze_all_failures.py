"""R15 测试工程师：分析所有失败函数的失败模式分类。"""
import sys
import types
import marshal
import dis
from collections import Counter

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r15_decompiled.py'


def load_pyc_code_objects(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        code = marshal.load(f)
    result = {}
    _collect(code, result, prefix='')
    return result


def _collect(code, result, prefix):
    if not prefix:
        name = '<module>'
    else:
        name = prefix + '.' + code.co_name
    result[name] = code
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            _collect(c, result, name)


def load_src_code_objects(src_path):
    with open(src_path, 'r', encoding='utf-8') as f:
        src = f.read()
    code = compile(src, src_path, 'exec')
    result = {}
    _collect(code, result, prefix='')
    return result


def get_instr_list(code):
    instrs = []
    for ins in dis.get_instructions(code):
        instrs.append((ins.offset, ins.opname, repr(ins.argval)[:60]))
    return instrs


def find_first_diff(pc, sc):
    pi = get_instr_list(pc)
    si = get_instr_list(sc)
    n = min(len(pi), len(si))
    for i in range(n):
        if pi[i] != si[i]:
            pctx = pi[max(0, i-2):i+3]
            sctx = si[max(0, i-2):i+3]
            return (i, pi[i], si[i], pctx, sctx)
    if len(pi) != len(si):
        if len(pi) > len(si):
            return (n, pi[n], None, pi[max(0, n-2):n+3], si[max(0, n-2):n+3])
        else:
            return (n, None, si[n], pi[max(0, n-2):n+3], si[max(0, n-2):n+3])
    return None


def classify_diff(name, pc, sc, diff):
    """Classify the failure mode."""
    if diff is None:
        return 'exact_match'
    idx, pi, si, pctx, sctx = diff

    # Different opnames
    if pi and si and pi[1] != si[1]:
        return f'opname_diff:{pi[1]}_vs_{si[1]}'

    # Same opname, different argval
    if pi and si and pi[1] == si[1]:
        opname = pi[1]
        if 'JUMP' in opname:
            p_target = pi[2].strip("'")
            s_target = si[2].strip("'")
            if p_target.isdigit() and s_target.isdigit():
                delta = int(p_target) - int(s_target)
                return f'jump_target_diff:delta={delta:+d}'
            return 'jump_target_diff'
        if opname == 'FOR_ITER':
            return 'argval_diff:FOR_ITER'
        if opname in ('LOAD_CONST',):
            return f'const_value_diff:{pi[2]}_vs_{si[2]}'
        if opname in ('LOAD_FAST', 'STORE_FAST'):
            return f'var_name_diff:{pi[2]}_vs_{si[2]}'
        if opname in ('LOAD_GLOBAL', 'LOAD_ATTR', 'STORE_ATTR', 'LOAD_METHOD'):
            return f'name_diff:{pi[2]}_vs_{si[2]}'
        return f'argval_diff:{opname}'

    # One is None (length mismatch)
    if pi is None:
        return f'extra_in_src:{si[1]}'
    if si is None:
        return f'extra_in_pyc:{pi[1]}'

    return 'unknown'


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    common = set(pyc_codes.keys()) & set(src_codes.keys())

    fail_modes = Counter()
    fail_details = {}

    for name in sorted(common):
        pc = pyc_codes[name]
        sc = src_codes[name]
        if pc.co_code == sc.co_code:
            continue
        diff = find_first_diff(pc, sc)
        if diff is None:
            continue
        mode = classify_diff(name, pc, sc, diff)
        fail_modes[mode] += 1
        fail_details.setdefault(mode, []).append((name, diff))

    print(f"=== 失败模式分类 ({sum(fail_modes.values())} 个失败函数) ===\n")
    for mode, cnt in fail_modes.most_common():
        print(f"  {mode}: {cnt} 个函数")

    # Show details for top failure modes
    for mode, cnt in fail_modes.most_common(5):
        print(f"\n--- {mode} 详情 ({cnt}) ---")
        for name, diff in fail_details[mode][:5]:
            idx, pi, si, pctx, sctx = diff
            print(f"  {name}")
            if pi:
                print(f"    pyc: {pi}")
            if si:
                print(f"    src: {si}")


if __name__ == '__main__':
    main()
