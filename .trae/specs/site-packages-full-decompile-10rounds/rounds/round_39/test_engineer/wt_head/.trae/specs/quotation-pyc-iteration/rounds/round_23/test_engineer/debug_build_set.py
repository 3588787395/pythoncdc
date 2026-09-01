"""R23-N8: 查看 build_future_fill_time 中 set() 字面量问题"""
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


def main():
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    target = find_code_obj(code_obj, 'build_future_fill_time')

    with open(SRC, 'r') as f:
        src = f.read()
    src_co = compile(src, '<decompiled>', 'exec')
    src_target = find_code_obj(src_co, 'build_future_fill_time')

    pi = get_instr_list(target)
    si = get_instr_list(src_target)

    print(f"pyc={len(pi)} instrs, src={len(si)} instrs")

    # Find BUILD_SET in pyc
    print(f"\n=== PYC BUILD_SET locations ===")
    for i, (off, op, av) in enumerate(pi):
        if op == 'BUILD_SET':
            print(f"  [{i}] {off} {op} {av}")

    print(f"\n=== SRC set() / BUILD_SET locations ===")
    for i, (off, op, av) in enumerate(si):
        if op == 'BUILD_SET' or (op == 'LOAD_GLOBAL' and av == 'set'):
            print(f"  [{i}] {off} {op} {av}")

    # Show context around offset 2290 in pyc (the diff point)
    print(f"\n=== PYC around offset 2290 ===")
    for i, (off, op, av) in enumerate(pi):
        if 2270 <= off <= 2320:
            print(f"  [{i}] {off} {op} {av}")

    # Show context around the matching src idx
    # Find the first diff
    diff_idx = None
    for i in range(min(len(pi), len(si))):
        if pi[i][1] != si[i][1] or pi[i][2] != si[i][2]:
            diff_idx = i
            break

    if diff_idx:
        print(f"\n=== First diff at idx {diff_idx} ===")
        start = max(0, diff_idx - 5)
        end_p = min(len(pi), diff_idx + 10)
        end_s = min(len(si), diff_idx + 10)
        print(f"  [PYC]")
        for j in range(start, end_p):
            mark = ">>" if j == diff_idx else "  "
            print(f"  {mark} [{j}] {pi[j][0]} {pi[j][1]} {pi[j][2]!r}")
        print(f"  [SRC]")
        for j in range(start, end_s):
            mark = ">>" if j == diff_idx else "  "
            print(f"  {mark} [{j}] {si[j][0]} {si[j][1]} {si[j][2]!r}")


if __name__ == '__main__':
    main()
