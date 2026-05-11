import sys; sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion
import dis

src = 'x = a and b'
code = compile(src, '<test>', 'exec')
print("=== Bytecode ===")
dis.dis(code)
print()

cfg = CFGBuilder().build(code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

for r in regions:
    if isinstance(r, BoolOpRegion):
        chain_info = [(b.start_offset, op) for b, op in r.op_chain]
        print(f"BoolOpRegion: entry={r.entry.start_offset}, chain={chain_info}, merge={r.merge_block.start_offset if r.merge_block else None}")
        print(f"  value_target={r.value_target}")
        print(f"  blocks={[b.start_offset for b in r.blocks]}")
