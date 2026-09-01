"""R30-8: dump get_valuation_new full bytecode."""
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
        if hasattr(const, 'co_name') and const.co_name == 'get_valuation_new':
            target = const
            break

    print(f"=== {target.co_name} (co_code len={len(target.co_code)}) ===")
    instrs = list(dis.get_instructions(target))
    for i, ins in enumerate(instrs):
        print(f"  [{i:3d}] off={ins.offset:4d} {ins.opname:30s} {repr(ins.argval)[:60]}")


if __name__ == '__main__':
    main()
