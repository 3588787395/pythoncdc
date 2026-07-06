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

for region in ra.regions:
    rtype = type(region).__name__
    entry_off = region.entry.start_offset if region.entry else None
    region_type = region.region_type
    blocks = sorted(b.start_offset for b in region.blocks) if region.blocks else []
    parent_type = type(region.parent).__name__ if region.parent else None
    print(f'{rtype}: entry={entry_off}, region_type={region_type}, blocks={blocks}, parent={parent_type}')

if os.path.exists(pyc): os.remove(pyc)
