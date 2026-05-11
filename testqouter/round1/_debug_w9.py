import py_compile, sys, os, marshal
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, WithRegion, Region, RegionType

tf = 'test_w03_multi_with.py'
pyc = tf+'c'
py_compile.compile(tf, cfile=pyc, doraise=True)
with open(pyc, 'rb') as f:
    f.read(16)
    code = marshal.load(f)
func_code = code.co_consts[0]
cfg = CFGBuilder().build(func_code)
ra = RegionAnalyzer(cfg)
ra.analyze()

gen = RegionASTGenerator(cfg, top_level_code=func_code)

top_level_regions = []
for r in ra.regions:
    is_contained = False
    for other in ra.regions:
        if other is not r and r.entry and r.entry in other.blocks:
            if not (isinstance(other, BoolOpRegion) and isinstance(r, LoopRegion)):
                is_contained = True
                break
    if not is_contained:
        top_level_regions.append(r)

print('Top-level regions:')
for r in top_level_regions:
    rtype = type(r).__name__
    entry_off = r.entry.start_offset if r.entry else None
    region_type = r.region_type
    blocks = sorted(b.start_offset for b in r.blocks) if r.blocks else []
    print(f'  {rtype}(entry={entry_off}, type={region_type}, blocks={blocks})')

print()
print('Processing order:')
for r in sorted(top_level_regions, key=lambda r: r.entry.start_offset if r.entry else 0):
    rtype = type(r).__name__
    entry_off = r.entry.start_offset if r.entry else None
    all_gen = all(b in gen.generated_blocks for b in r.blocks) if r.blocks else False
    print(f'  {rtype}(entry={entry_off}): all_gen={all_gen}')
    if not all_gen:
        result = gen._generate_region(r)
        if result is None:
            result = []
        if not isinstance(result, list):
            result = [result]
        stmt_types = [s.get('type', '?') if isinstance(s, dict) else str(s) for s in result]
        print(f'    -> {stmt_types}')

if os.path.exists(pyc): os.remove(pyc)
