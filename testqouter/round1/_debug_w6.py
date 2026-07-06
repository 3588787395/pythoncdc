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
        print(f'WithRegion blocks: {sorted(b.start_offset for b in region.blocks)}')
        result = gen._generate_with_impl(region)
        if isinstance(result, list):
            for item in result:
                t = item.get('type', '?')
                if t == 'With':
                    print(f'  With: {len(item.get("items",[]))} items')
                    for s in item.get('body', []):
                        print(f'    body: {s.get("type","?")}')
                elif t == 'Assign':
                    tgt = item.get('targets', [{}])[0]
                    tgt_id = tgt.get('id', '?') if isinstance(tgt, dict) else '?'
                    print(f'  Assign: {tgt_id}')
                elif t == 'Return':
                    print(f'  Return')
                elif t == 'Expr':
                    print(f'  Expr')
                else:
                    print(f'  {t}')
        elif isinstance(result, dict):
            t = result.get('type', '?')
            print(f'  {t}')
        print(f'  generated_blocks after with: {sorted(b.start_offset for b in gen.generated_blocks)}')
        break

if os.path.exists(pyc): os.remove(pyc)
