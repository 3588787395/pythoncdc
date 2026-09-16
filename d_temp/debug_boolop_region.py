import sys, marshal, types
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg.cfg_builder import ControlFlowGraph
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion, IfRegion

with open(r'F:\Downloads\pythoncdc-main\site-packages\IQData\utils\common_func.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

for const in code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'handle_exrights':
        cfg = ControlFlowGraph(const)
        analyzer = RegionAnalyzer(cfg)
        analyzer.analyze()
        
        for r in analyzer.regions:
            if isinstance(r, BoolOpRegion):
                print(f"BoolOpRegion@{r.entry.start_offset}:")
                print(f"  op_chain={[(b.start_offset, op) for b, op in r.op_chain]}")
                print(f"  merge_block={r.merge_block.start_offset if r.merge_block else None}")
                print()
            if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 0:
                print(f"IfRegion@0:")
                print(f"  entry={r.entry.start_offset}")
                print(f"  cond_block={r.condition_block.start_offset if r.condition_block else None}")
                ibc = getattr(r, 'inline_boolop_chains', {})
                for k, v in ibc.items():
                    print(f"  inline_boolop_chains key={k}:")
                    print(f"    op={v['op']}, blocks={[(b.start_offset, b.get_last_instruction().opname) for b in v['blocks']]}")
                print(f"  then={[b.start_offset for b in r.then_blocks]}")
                print(f"  else={[b.start_offset for b in r.else_blocks]}")
                print(f"  merge={r.merge_block.start_offset if r.merge_block else None}")
