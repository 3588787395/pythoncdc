import sys, marshal, types
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg.cfg_builder import ControlFlowGraph
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion, IfRegion

with open(r'F:\Downloads\pythoncdc-main\site-packages\IQData\utils\common_func.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

exrights_code = code.co_consts[32]
print("Found handle_exrights code object")
print("co_consts count:", len(exrights_code.co_consts))

cfg = ControlFlowGraph(exrights_code)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print("Total regions:", len(analyzer.regions))
for r in analyzer.regions:
    if isinstance(r, BoolOpRegion):
        chain_info = [(b.start_offset, op) for b, op in r.op_chain]
        merge_off = r.merge_block.start_offset if r.merge_block else None
        print("BoolOpRegion@{}: op_chain={}, merge={}".format(r.entry.start_offset, chain_info, merge_off))
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 0:
        cond_off = r.condition_block.start_offset if r.condition_block else None
        print("IfRegion@0: cond={}".format(cond_off))
        ibc = getattr(r, 'inline_boolop_chains', {})
        for k, v in ibc.items():
            blocks_info = [(b.start_offset, b.get_last_instruction().opname) for b in v['blocks']]
            print("  ibc key={}: op={}, blocks={}".format(k, v['op'], blocks_info))
        then_offs = [b.start_offset for b in r.then_blocks]
        else_offs = [b.start_offset for b in r.else_blocks]
        merge_off = r.merge_block.start_offset if r.merge_block else None
        print("  then={}, else={}, merge={}".format(then_offs, else_offs, merge_off))
