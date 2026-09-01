"""分析api_get_financial的CFG块结构"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg

PYC = '/workspace/quotation.pyc'


def main():
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    # Find api_get_financial
    target = None
    def walk(co):
        nonlocal target
        if co.co_name == 'api_get_financial':
            target = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                walk(const)
    walk(code_obj)

    if not target:
        print("api_get_financial not found")
        return

    cfg = build_cfg(target)
    blocks = sorted(cfg.blocks.values(), key=lambda b: b.start_offset)

    print(f"=== CFG blocks ({len(blocks)}) ===")
    for b in blocks:
        ins_str = ', '.join(f"{i.opname}({i.argval!r})" for i in b.instructions[:5])
        succs = [s.id for s in b.successors]
        preds = [p.id for p in b.predecessors]
        print(f"  B{b.id} (off {b.start_offset}) [{ins_str}...] succs={succs} preds={preds}")

    # Print blocks around offset 552 (SWAP) and 554 (POP_EXCEPT)
    print("\n=== Blocks around offset 540-580 ===")
    for b in blocks:
        if 440 <= b.start_offset <= 580:
            print(f"\n--- B{b.id} (off {b.start_offset}) ---")
            for ins in b.instructions:
                print(f"  {ins.offset:4d} {ins.opname:30s} {ins.argval!r}")
            print(f"  succs: {[s.id for s in b.successors]}")


if __name__ == '__main__':
    main()
