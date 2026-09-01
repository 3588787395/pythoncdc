"""R30-6: dump change_his_to_forward full if-elif chain bytecode."""
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
    # Print instructions from offset 1380 to 1560 to find B's body and C's start
    print("--- offsets 1380 to 1560 ---")
    for i, ins in enumerate(instrs):
        if 1380 <= ins.offset <= 1560:
            print(f"  [{i:3d}] off={ins.offset:4d} {ins.opname:35s} {repr(ins.argval)[:60]}")


if __name__ == '__main__':
    main()
