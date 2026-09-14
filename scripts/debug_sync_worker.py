import sys
sys.path.insert(0, '.')
from pycdc import decompile_pyc
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.cfg_builder import CFGBuilder
from core.pyc_loader_v2 import load_pyc_file_v2

pyc_data = load_pyc_file_v2('site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc')
code_obj = pyc_data.code

# Find _sync_worker
def find_func(c, name):
    obj = c.obj if hasattr(c, 'obj') else c
    if hasattr(obj, 'name') and obj.name == name: return obj
    if hasattr(obj, 'co_name') and obj.co_name == name: return obj
    for cc in (getattr(obj, 'consts', []) or []):
        r = find_func(cc, name)
        if r: return r
    return None

sync_code = find_func(code_obj, '_sync_worker')
if sync_code is None:
    print('_sync_worker not found')
    sys.exit(1)

print('Found _sync_worker')
print('co_varnames:', sync_code.co_varnames[:20])

# Build CFG and analyze
from core.control_flow import ControlFlowGraph
cfg = ControlFlowGraph()
blocks = cfg.build_from_code(sync_code)

analyzer = RegionAnalyzer(cfg, sync_code)
analyzer.analyze()

# Find the IfRegion with condition block at offset 362
for r in analyzer.regions:
    if hasattr(r, 'condition_block') and r.condition_block is not None:
        if r.condition_block.start_offset == 362:
            print(f'\nIfRegion entry={r.entry.start_offset}, cond={r.condition_block.start_offset}')
            print(f'  then_blocks: {[b.start_offset for b in r.then_blocks]}')
            print(f'  else_blocks: {[b.start_offset for b in r.else_blocks]}')
            print(f'  merge_block: {r.merge_block.start_offset if r.merge_block else None}')
            cond_last = r.condition_block.get_last_instruction()
            print(f'  cond_last: {cond_last.opname} {cond_last.argval}')
            
            # Check what _then_entry_offsets_excluding_connectors returns
            from core.cfg.region_ast_generator import RegionASTGenerator
            gen = RegionASTGenerator(cfg, sync_code, analyzer, sync_code)
            offsets = gen._then_entry_offsets_excluding_connectors(r)
            print(f'  then_entry_offsets: {offsets}')
            
            jump_target = cond_last.argval
            print(f'  jump_target={jump_target}, in then_offsets={jump_target in offsets}')
            
            if_true = 'IF_TRUE' in cond_last.opname
            jumps_to_then = jump_target in offsets
            negate = jumps_to_then != if_true
            print(f'  if_true={if_true}, jumps_to_then={jumps_to_then}, negate={negate}')
