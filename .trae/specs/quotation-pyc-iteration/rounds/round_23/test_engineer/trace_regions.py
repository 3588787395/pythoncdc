"""R23 测试工程师：追踪get_trading_day_by_date的区域分析"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion, IfRegion

PYC = '/workspace/quotation.pyc'


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
    pyc_codes = load_pyc_code_objects(PYC)
    co = pyc_codes['get_trading_day_by_date']

    builder = CFGBuilder()
    cfg = builder.build(co)

    print("=== CFG Blocks ===")
    for block in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
        last = block.get_last_instruction()
        print(f"\nBlock {block.id} (offset={block.start_offset}):")
        for ins in block.instructions:
            if ins.opname in ('EXTENDED_ARG', 'CACHE'):
                continue
            print(f"  {ins.offset:4d}  {ins.opname:35s} {ins.argval!r}")
        if last:
            print(f"  -> successors: {[s.id for s in block.successors]}")
            print(f"  -> cond_successors: {[s.id for s in block.conditional_successors]}")

    analyzer = RegionAnalyzer(cfg)
    regions = analyzer.analyze()

    print(f"\n=== Regions ({len(regions)}) ===")
    for r in regions:
        print(f"\n{type(r).__name__}:")
        print(f"  entry={r.entry.id if r.entry else None}")
        print(f"  blocks={[b.id for b in r.blocks]}")
        if hasattr(r, 'op_chain'):
            print(f"  op_chain={[(b.id, op) for b, op in r.op_chain]}")
        if hasattr(r, 'merge_block') and r.merge_block:
            print(f"  merge_block={r.merge_block.id}")
        if hasattr(r, 'condition_block') and r.condition_block:
            print(f"  condition_block={r.condition_block.id}")
        if hasattr(r, 'then_blocks'):
            print(f"  then_blocks={[b.id for b in r.then_blocks]}")
        if hasattr(r, 'else_blocks'):
            print(f"  else_blocks={[b.id for b in r.else_blocks]}")

    print(f"\n=== block_to_region ===")
    for block in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
        reg = analyzer.block_to_region.get(block)
        if reg:
            print(f"  Block {block.id} (offset={block.start_offset}) -> {type(reg).__name__}(entry={reg.entry.id})")


if __name__ == '__main__':
    main()
