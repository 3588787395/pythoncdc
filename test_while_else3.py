import sys
sys.path.insert(0, '.')
import marshal

pyc_path = 'site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

# Find the function that contains the problematic while-else
# Look for the _monitor_trade_status or similar function
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion

def find_while_else_issues(code_obj, prefix=''):
    for const in code_obj.co_consts:
        if hasattr(const, 'co_code'):
            find_while_else_issues(const, prefix + '  ')
    
    cfg = build_cfg(code_obj)
    analyzer = RegionAnalyzer(cfg)
    regions = analyzer.analyze()
    
    for r in regions:
        if isinstance(r, LoopRegion) and r.else_blocks:
            # Check if else_blocks contain code that would be in the else clause
            has_break = r.has_break
            else_blocks = r.else_blocks
            # Check if break_blocks contain something other than what we expect
            break_blocks = r.break_blocks
            
            # Debug output for loops with else
            print(f'{prefix}LoopRegion in {code_obj.co_name}:')
            print(f'{prefix}  header={r.header_block.start_offset if r.header_block else None}')
            print(f'{prefix}  condition_block={r.condition_block.start_offset if r.condition_block else None}')
            print(f'{prefix}  body_blocks={[b.start_offset for b in r.body_blocks]}')
            print(f'{prefix}  else_blocks={[b.start_offset for b in else_blocks] if else_blocks else None}')
            print(f'{prefix}  break_blocks={[b.start_offset for b in break_blocks] if break_blocks else []}')
            print(f'{prefix}  has_break={has_break}')
            
            # Check for problematic patterns: else block that contains return but is in body
            if else_blocks and has_break:
                for eb in else_blocks:
                    for instr in eb.instructions:
                        if instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                            print(f'{prefix}  ELSE BLOCK HAS RETURN: {instr}')
            
            print()

find_while_else_issues(code)
