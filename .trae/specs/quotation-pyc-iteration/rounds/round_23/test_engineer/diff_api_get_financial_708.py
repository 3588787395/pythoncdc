"""R23-N6: 查看 api_get_financial 中 offset 708 附近的字节码差异"""
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

    target = find_code_obj(code_obj, 'api_get_financial')

    with open(SRC, 'r') as f:
        src = f.read()
    src_co = compile(src, '<decompiled>', 'exec')
    src_target = find_code_obj(src_co, 'api_get_financial')

    pi = get_instr_list(target)
    si = get_instr_list(src_target)

    print(f"pyc={len(pi)} instrs, src={len(si)} instrs")

    # 找 offset 708 附近
    print(f"\n=== PYC around 708 ===")
    for i, (off, op, av) in enumerate(pi):
        if 660 <= off <= 760:
            print(f"  [{i}] {off:>5} {op:<30} {av!r}")

    print(f"\n=== SRC around 708 (idx matching) ===")
    # Find the idx where PYC has offset 708
    pyc_idx_708 = None
    for i, (off, op, av) in enumerate(pi):
        if off == 708:
            pyc_idx_708 = i
            break
    if pyc_idx_708 is None:
        print("708 not found in PYC")
        return

    # Show SRC around the same idx
    start = max(0, pyc_idx_708 - 15)
    end = min(len(si), pyc_idx_708 + 15)
    for j in range(start, end):
        mark = ">>" if j == pyc_idx_708 else "  "
        print(f"  {mark} [{j}] {si[j][0]:>5} {si[j][1]:<30} {si[j][2]!r}")


if __name__ == '__main__':
    main()
