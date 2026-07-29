"""调试脚本：对 quotation.pyc 指定函数构建 CFG + 区域归约，dump 区域树 + 块结构。

用法：python debug_quotation_regions.py <func_name> [<func_name2> ...]
"""
import sys
import types
import dis

sys.path.insert(0, '/workspace')

from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.pyc_loader_v2 import load_pyc_file_v2


def dump_cfg_blocks(cfg, name, out):
    print(f"\n===== CFG BLOCKS for {name} =====", file=out)
    blocks = cfg.blocks.values() if isinstance(cfg.blocks, dict) else cfg.blocks
    for blk in sorted(blocks, key=lambda b: b.start_offset):
        last = blk.get_last_instruction()
        last_str = f"{last.opname} {last.argval}" if last else "<none>"
        preds = sorted(p.start_offset for p in blk.predecessors)
        succs = sorted(s.start_offset for s in blk.successors)
        instrs = []
        for ins in blk.instructions:
            if ins.opname in ('EXTENDED_ARG', 'CACHE', 'NOP', 'RESUME'):
                continue
            instrs.append(f"{ins.offset}:{ins.opname}({ins.argval})")
        print(f"  blk@{blk.start_offset} last=[{last_str}] preds={preds} succs={succs}", file=out)
        print(f"    instrs: {' | '.join(instrs[:10])}{' ...' if len(instrs)>10 else ''}", file=out)


def dump_regions(analyzer, name, out):
    print(f"\n===== REGIONS for {name} =====", file=out)
    for i, region in enumerate(analyzer.regions):
        rtype = region.region_type
        entry = region.entry.start_offset if region.entry else None
        blocks = sorted(b.start_offset for b in region.blocks) if hasattr(region, 'blocks') else []
        extra = ''
        if hasattr(region, 'header_block') and region.header_block:
            extra += f" header={region.header_block.start_offset}"
        if hasattr(region, 'body_blocks') and region.body_blocks:
            extra += f" body={sorted(b.start_offset for b in region.body_blocks)}"
        if hasattr(region, 'condition_block') and region.condition_block:
            extra += f" cond={region.condition_block.start_offset}"
        if hasattr(region, 'then_blocks') and region.then_blocks:
            extra += f" then={sorted(b.start_offset for b in region.then_blocks)}"
        if hasattr(region, 'else_blocks') and region.else_blocks:
            extra += f" else={sorted(b.start_offset for b in region.else_blocks)}"
        if hasattr(region, 'back_edge_block') and region.back_edge_block:
            extra += f" backedge={region.back_edge_block.start_offset}"
        if hasattr(region, 'exit_block') and region.exit_block:
            extra += f" exit={region.exit_block.start_offset}"
        print(f"  [{i}] {rtype} entry={entry} blocks={blocks}{extra}", file=out)
    print(f"\n----- block_to_region -----", file=out)
    for blk, reg in sorted(analyzer.block_to_region.items(), key=lambda x: x[0].start_offset):
        rentry = reg.entry.start_offset if reg.entry else None
        print(f"  blk@{blk.start_offset} -> {reg.region_type} (entry={rentry})", file=out)


def main():
    targets = set(sys.argv[1:]) or {'build_future_fill_time'}
    module = load_pyc_file_v2('/workspace/quotation.pyc')
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    out = sys.stdout

    def walk(co, prefix=''):
        name = '<module>' if (co.co_name == '<module>' and not prefix) else prefix + co.co_name
        if name in targets or co.co_name in targets:
            print(f"\n########## {name} ##########", file=out)
            cfg = build_cfg(co)
            dump_cfg_blocks(cfg, name, out)
            analyzer = RegionAnalyzer(cfg)
            analyzer.analyze()
            dump_regions(analyzer, name, out)
        sub = '' if name == '<module>' else name + '.'
        for c in co.co_consts:
            if isinstance(c, types.CodeType):
                walk(c, sub)

    walk(code_obj)


if __name__ == '__main__':
    main()
