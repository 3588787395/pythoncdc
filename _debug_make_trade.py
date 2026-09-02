import os, sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.cfg_builder import ControlFlowGraph
import marshal, types
f=open(r'F:\Downloads\pythoncdc-main\site-packages\IQEngine\plugins\plugin_system_accounts\position_model\stock_position.pyc','rb')
f.read(16)
code=marshal.load(f)
f.close()
cls=[c for c in code.co_consts if isinstance(c, types.CodeType) and c.co_name=='StockPosition'][0]
mt=[c for c in cls.co_consts if isinstance(c, types.CodeType) and c.co_name=='make_trade'][0]
print(f"Code object: {mt.co_name}, nconsts={len(mt.co_consts)}")
cfg = ControlFlowGraph(mt)
print(f"CFG blocks: {len(cfg.blocks)}")
for b in cfg.blocks:
    last = b.get_last_instruction()
    last_str = f"{last.opname} to {last.argval}" if last else "None"
    print(f"  Block {b.start_offset}: last={last_str}")
gen = RegionASTGenerator(cfg)
regions = gen.region_analyzer.analyze()
print(f"Regions found: {len(regions)}")
for r in regions:
    entry_off = r.entry.start_offset if r.entry else None
    rtype = type(r).__name__
    ibc = getattr(r, 'inline_boolop_chains', None)
    cb_off = getattr(r, 'condition_block', None)
    if cb_off:
        cb_off = cb_off.start_offset
    print(f"  {rtype} entry={entry_off} cond_block={cb_off} ibc={bool(ibc)}")
    if ibc:
        for k, v in ibc.items():
            blist = [b.start_offset for b in v.get('blocks', [])]
            op = v.get('op')
            print(f"    key={k} blocks={blist} op={op}")
