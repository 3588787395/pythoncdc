"""Temporary diagnostic: dump all regions for with_in_match."""
import sys, marshal
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")

f = open(r"F:\Downloads\pythoncdc-main\test_repros\round2\x05_with_deep_hosts.pyc", 'rb'); f.read(16)
module_code = marshal.load(f)
FUNC = sys.argv[1] if len(sys.argv) > 1 else 'with_in_match'
target = [c for c in module_code.co_consts if hasattr(c, 'co_name') and c.co_name == FUNC][0]

from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

cfg = build_cfg(target)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

def show(r, indent="  "):
    blocks = sorted(b.start_offset for b in r.blocks)
    entry = r.entry.start_offset if getattr(r, 'entry', None) is not None else None
    extra = ''
    if type(r).__name__ == 'WithRegion':
        extra = f" items_var={[getattr(i, 'argval', None) for i in getattr(r, 'items', [])]}" if hasattr(r, 'items') else ''
    print(f"{indent}{type(r).__name__} entry={entry} blocks={blocks}{extra}")
    for c in getattr(r, 'children', None) or []:
        show(c, indent + "    ")

print("=== ALL REGIONS ===")
for r in regions:
    show(r)

print("=== block_to_region ===")
for b in sorted(analyzer.block_to_region, key=lambda x: x.start_offset):
    reg = analyzer.block_to_region[b]
    print(f"  B{b.start_offset} -> {type(reg).__name__} entry={reg.entry.start_offset if reg.entry else None}")

print("=== block_roles ===")
for off in sorted(analyzer.block_roles):
    print(f"  B{off} -> {analyzer.block_roles[off]}")
