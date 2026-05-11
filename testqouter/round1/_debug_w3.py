import py_compile, sys, os, marshal
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, WithRegion

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

print('block_to_region mapping:')
for b in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
    region = ra.block_to_region.get(b)
    if region:
        print(f'  block {b.start_offset} -> {type(region).__name__}(entry={region.entry.start_offset})')
    else:
        print(f'  block {b.start_offset} -> None (ORPHAN)')

print()
print('All CFG blocks:')
for b in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
    print(f'  block {b.start_offset}')

if os.path.exists(pyc): os.remove(pyc)
