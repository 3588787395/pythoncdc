"""R23-N6: 查看 valuation 中 offset 940 附近的字节码差异 (JUMP_BACKWARD vs NOP)"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r23_decompiled.py'


def find_code_obj(co, name):
    for const in co.co_consts:
        if isinstance(const, type(co)):
            if const.co_name == name:
                return const
            sub = find_code_obj(const, name)
            if sub:
                return sub
    return None


def get_instr_list(co):
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def diff_function(name, n_ctx=12):
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    target = find_code_obj(code_obj, name)

    with open(SRC, 'r') as f:
        src = f.read()
    src_co = compile(src, '<decompiled>', 'exec')
    src_target = find_code_obj(src_co, name)

    pi = get_instr_list(target)
    si = get_instr_list(src_target)

    print(f"\n{'='*80}\n{name}: pyc={len(pi)} instrs, src={len(si)} instrs\n{'='*80}")

    # Find first diff
    diff_idx = None
    n = min(len(pi), len(si))
    for i in range(n):
        if pi[i][1] != si[i][1] or pi[i][2] != si[i][2]:
            diff_idx = i
            break
    if diff_idx is None and len(pi) != len(si):
        diff_idx = n

    if diff_idx is None:
        print("  (无差异)")
        return

    start = max(0, diff_idx - n_ctx)
    end_p = min(len(pi), diff_idx + n_ctx + 1)
    end_s = min(len(si), diff_idx + n_ctx + 1)
    print(f"\n  -- 差异点 idx={diff_idx} --")
    print(f"  [PYC]")
    for j in range(start, end_p):
        mark = ">>" if j == diff_idx else "  "
        print(f"  {mark} [{j}] {pi[j][0]:>5} {pi[j][1]:<30} {pi[j][2]!r}")
    print(f"  [SRC]")
    for j in range(start, end_s):
        mark = ">>" if j == diff_idx else "  "
        print(f"  {mark} [{j}] {si[j][0]:>5} {si[j][1]:<30} {si[j][2]!r}")


if __name__ == '__main__':
    diff_function('valuation')
    diff_function('build_future_fill_time')
    diff_function('get_valuation_new')
