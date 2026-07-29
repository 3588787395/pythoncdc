"""R14 测试工程师：分析 argval_diff:FOR_ITER 失败函数。"""
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
            pctx = pi[max(0, i-3):i+4]
            sctx = si[max(0, i-3):i+4]
            return (i, pi[i], si[i], pctx, sctx)
    if len(pi) != len(si):
        if len(pi) > len(si):
            return (n, pi[n], None, pi[max(0, n-3):n+4], si[max(0, n-3):n+4])
        else:
            return (n, None, si[n], pi[max(0, n-3):n+4], si[max(0, n-3):n+4])
    return None


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    common = set(pyc_codes.keys()) & set(src_codes.keys())
    for_iter_funcs = []

    for name in sorted(common):
        pc = pyc_codes[name]
        sc = src_codes[name]
        if pc.co_code == sc.co_code:
            continue
        diff = find_first_diff(pc, sc)
        if diff is None:
            continue
        idx, pi, si, pctx, sctx = diff
        if pi and si and pi[1] == si[1] and pi[1] == 'FOR_ITER':
            for_iter_funcs.append((name, pi, si, pctx, sctx))

    print(f"=== argval_diff:FOR_ITER 函数列表 ({len(for_iter_funcs)}) ===")
    for name, pi, si, pctx, sctx in for_iter_funcs:
        print(f"\n  {name}")
        print(f"    pyc: {pi}")
        print(f"    src: {si}")
        print(f"    pyc ctx:")
        for c in pctx:
            print(f"      {c}")
        print(f"    src ctx:")
        for c in sctx:
            print(f"      {c}")


if __name__ == '__main__':
    main()
