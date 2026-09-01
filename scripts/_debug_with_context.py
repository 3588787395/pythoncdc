import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
import dis, marshal, types

with open('site-packages/IQEngine/plugins/plugin_system_risk_calculation/function.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(c, name):
    if c.co_name == name: return c
    for const in c.co_consts:
        if isinstance(const, types.CodeType):
            r = find_code(const, name)
            if r: return r
    return None

c = find_code(code, 'backtest_info_writer')
print(f'Found: {c.co_name}')

builder = CFGBuilder()
cfg = builder.build(c)

ra = RegionAnalyzer(cfg)
ra.analyze()

# Find WithRegion
for r in ra.regions:
    if type(r).__name__ == 'WithRegion':
        print(f'\nWithRegion found:')
        print(f'  entry: {r.entry.id if r.entry else None}')
        print(f'  items: {len(r.items) if r.items else 0}')
        if r.items:
            for i, (ctx_instrs, tgt) in enumerate(r.items):
                print(f'  item {i}: target={tgt}')
                print(f'    context_instrs ({len(ctx_instrs)}):')
                for instr in ctx_instrs:
                    print(f'      {instr.opname} {instr.argval if hasattr(instr, "argval") else instr.arg}')
        print(f'  with_blocks: {[b.id for b in r.with_blocks] if r.with_blocks else []}')
        print(f'  cleanup_blocks: {[b.id for b in r.cleanup_blocks] if r.cleanup_blocks else []}')
        print(f'  target: {r.target}')
        print(f'  is_async: {r.is_async}')
