"""R28 测试工程师：调试 cash_collection_ability 的 BoolOp 链检测"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion, IfRegion


def load_pyc_code_objects(pyc_path):
    module = load_pyc_file_v2(pyc_path)
    if not module:
        return {}
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    result = {}
    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        result[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)
    walk(code_obj)
    return result


def main():
    pyc_codes = load_pyc_code_objects('/workspace/quotation.pyc')
    co = pyc_codes['cash_collection_ability']
    print(f"=== cash_collection_ability bytecode (前60条) ===")
    for i, ins in enumerate(dis.get_instructions(co)):
        if i >= 70:
            break
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        print(f"  {ins.offset:>4} {ins.opname:<30} {ins.argval}")

    print(f"\n=== CFG blocks (前25) ===")
    builder = CFGBuilder()
    cfg = builder.build(co)
    blocks_list = list(cfg.get_blocks_in_order())
    for i, b in enumerate(blocks_list):
        if i >= 25:
            break
        last = b.get_last_instruction()
        last_str = f"{last.opname} {last.argval}" if last else "None"
        succs = [s.start_offset for s in b.successors]
        print(f"  block@{b.start_offset}: last={last_str}, succs={succs}")
        for ins in b.instructions:
            if ins.opname in ('EXTENDED_ARG', 'CACHE', 'NOP', 'RESUME'):
                continue
            print(f"    {ins.offset:>4} {ins.opname:<28} {ins.argval}")

    print(f"\n=== Regions ===")
    analyzer = RegionAnalyzer(cfg)
    regions = analyzer.analyze()
    for r in regions:
        blocks_str = [b.start_offset for b in r.blocks]
        print(f"  {type(r).__name__}: entry={r.entry.start_offset}, blocks={blocks_str}")
        if hasattr(r, 'op_chain') and r.op_chain:
            print(f"    op_chain: {[(b.start_offset, op) for b, op in r.op_chain]}")
        if hasattr(r, 'then_blocks') and r.then_blocks:
            print(f"    then_blocks: {[b.start_offset for b in r.then_blocks]}")
        if hasattr(r, 'else_blocks') and r.else_blocks:
            print(f"    else_blocks: {[b.start_offset for b in r.else_blocks]}")
        if hasattr(r, 'merge_block') and r.merge_block:
            print(f"    merge_block: {r.merge_block.start_offset}")

    # 检查 block@140 和 block@144 的跳转目标
    print(f"\n=== Block@140 / @144 jump targets ===")
    for offset in [140, 144, 282, 362]:
        b = cfg.get_block_by_offset(offset)
        if b is None:
            print(f"  block@{offset}: NOT FOUND")
            continue
        last = b.get_last_instruction()
        last_str = f"{last.opname} {last.argval}" if last else "None"
        succs = [s.start_offset for s in b.successors]
        print(f"  block@{offset}: last={last_str}, succs={succs}")

    # 282 和 362 的 last instruction
    print(f"\n=== Block@282 / @362 last instr (for op_type decision) ===")
    for offset in [282, 362]:
        b = cfg.get_block_by_offset(offset)
        if b is None:
            print(f"  block@{offset}: NOT FOUND")
            continue
        last = b.get_last_instruction()
        last_str = f"{last.opname} {last.argval}" if last else "None"
        print(f"  block@{offset}: last={last_str}")


if __name__ == '__main__':
    main()
