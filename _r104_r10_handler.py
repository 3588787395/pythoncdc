import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
import marshal

path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_10_try_wrap_for_else_break.pyc'
with open(path, 'rb') as f:
    f.read(4); f.read(4); f.read(8)
    code = marshal.load(f)

func_code = code.co_consts[1]
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(func_code)

region_analyzer = RegionAnalyzer(cfg)
regions = region_analyzer.analyze()

for region in regions:
    if type(region).__name__ == 'TryExceptRegion':
        print(f'TryExceptRegion:')
        print(f'  try_blocks: {[b.id for b in region.try_blocks]}')
        print(f'  handler_entry_blocks: {[b.id for b in region.handler_entry_blocks]}')
        print(f'  except_handlers: {region.except_handlers}')
        
        # Check handler_blocks
        for i, handler in enumerate(region.except_handlers):
            exc_type, exc_name, body_blocks = handler
            print(f'\n  Handler {i}: {exc_type} as {exc_name}')
            print(f'    body_blocks: {[b.id for b in body_blocks]}')
            for b in body_blocks:
                print(f'    block {b.id}: {[(i.opname, i.arg) for i in b.instructions]}')
                print(f'      successors: {[s.id for s in b.successors]}')
