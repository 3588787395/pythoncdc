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
    if isinstance(region, WithRegion):
        result = gen._generate_with_impl(region)
        print(f'After WithRegion, generated_blocks: {sorted(b.start_offset for b in gen.generated_blocks)}')
        break

for region in ra.regions:
    if isinstance(region, Region) and region.entry and region.entry.start_offset == 438:
        print(f'\nProcessing Region(entry=438):')
        print(f'  blocks: {sorted(b.start_offset for b in region.blocks)}')
        for b in sorted(region.blocks, key=lambda b: b.start_offset):
            print(f'  block {b.start_offset} in generated_blocks: {b in gen.generated_blocks}')
        result = gen._generate_basic_region(region)
        print(f'  Result: {len(result)} statements')
        for s in result:
            t = s.get('type', '?')
            if t == 'Assign':
                tgt = s.get('targets', [{}])[0]
                tgt_id = tgt.get('id', '?') if isinstance(tgt, dict) else '?'
                print(f'    Assign: {tgt_id}')
            elif t == 'Return':
                print(f'    Return')
            elif t == 'Expr':
                print(f'    Expr')
            else:
                print(f'    {t}')
        break

if os.path.exists(pyc): os.remove(pyc)
