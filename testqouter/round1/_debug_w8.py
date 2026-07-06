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

for region in ra.regions:
    rtype = type(region).__name__
    entry_off = region.entry.start_offset if region.entry else None
    region_type = region.region_type
    result = gen._generate_region(region)
    if result is None:
        result = []
    if not isinstance(result, list):
        result = [result]
    stmt_types = [s.get('type', '?') if isinstance(s, dict) else str(s) for s in result]
    print(f'{rtype}(entry={entry_off}): {stmt_types}')

if os.path.exists(pyc): os.remove(pyc)
