"""R14 测试工程师：分析所有 jump_target_diff 失败函数的详细差异。"""
import sys
import types
import marshal
import dis
from collections import Counter

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r14_decompiled.py'


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


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    common = set(pyc_codes.keys()) & set(src_codes.keys())
    jt_diff_funcs = []

    for name in sorted(common):
        pc = pyc_codes[name]
        sc = src_codes[name]
        # Skip exact matches
        if pc.co_code == sc.co_code:
            continue
        diff = find_first_diff(pc, sc)
        if diff is None:
            continue
        idx, pi, si, pctx, sctx = diff
        if pi and si and pi[1] == si[1] and 'JUMP' in pi[1]:
            jt_diff_funcs.append((name, pi, si, pctx, sctx))

    print(f"=== jump_target_diff 函数列表 ({len(jt_diff_funcs)}) ===")
    # 按差异类型分组
    delta_counter = Counter()
    for name, pi, si, pctx, sctx in jt_diff_funcs:
        p_target = int(pi[2].strip("'")) if pi[2].strip("'").isdigit() else 0
        s_target = int(si[2].strip("'")) if si[2].strip("'").isdigit() else 0
        delta = p_target - s_target
        delta_counter[delta] += 1

    print(f"\n--- 跳转目标偏移差分布 ---")
    for delta, cnt in delta_counter.most_common():
        print(f"  delta={delta:+d}: {cnt} 个函数")

    print(f"\n--- 前20个函数详情 ---")
    for name, pi, si, pctx, sctx in jt_diff_funcs[:20]:
        print(f"\n  {name}")
        print(f"    pyc: {pi}")
        print(f"    src: {si}")
        print(f"    pyc ctx: {pctx}")
        print(f"    src ctx: {sctx}")


if __name__ == '__main__':
    main()
