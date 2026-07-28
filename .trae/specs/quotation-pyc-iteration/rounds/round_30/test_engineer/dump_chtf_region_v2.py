"""R30-6: dump change_his_to_forward bytecode offsets around the diff region."""
import sys
import dis
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'


def main():
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    target = None
    for const in code_obj.co_consts:
        if hasattr(const, 'co_name') and const.co_name == 'change_his_to_forward':
            target = const
            break

    print(f"=== {target.co_name} ===")
    instrs = list(dis.get_instructions(target))
    # Print instructions from idx 320 to 345
    for i, ins in enumerate(instrs):
        if 320 <= i <= 345:
            print(f"  [{i:3d}] off={ins.offset:4d} {ins.opname:35s} {repr(ins.argval)[:60]}")
        if i > 345:
            break

    # Also dump around offset 1748 and 2306
    print("\n=== Around offset 1748 ===")
    for i, ins in enumerate(instrs):
        if 1740 <= ins.offset <= 1780:
            print(f"  [{i:3d}] off={ins.offset:4d} {ins.opname:35s} {repr(ins.argval)[:60]}")

    print("\n=== Around offset 2306 ===")
    for i, ins in enumerate(instrs):
        if 2300 <= ins.offset <= 2330:
            print(f"  [{i:3d}] off={ins.offset:4d} {ins.opname:35s} {repr(ins.argval)[:60]}")


if __name__ == '__main__':
    main()
