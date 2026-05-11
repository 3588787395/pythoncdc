import sys, os
sys.path.insert(0, r'f:\pythoncdc')
from core.cfg import build_cfg, CFGRegionAnalyzer
from core.cfg.region_ast_generator import generate_ast_from_regions
from core.cfg.code_generator import CodeGenerator
import py_compile, tempfile

src = "with open('f') as f:\n    for line in f:\n        print(line)"
with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
    f.write(src)
    tmp = f.name
pyc = tmp + 'c'
py_compile.compile(tmp, cfile=pyc, doraise=True)
code_obj = compile(src, tmp, 'exec')
cfg = build_cfg(code_obj)
ra = CFGRegionAnalyzer(cfg)
regions = ra.analyze()
print('Regions:')
for r in regions:
    print(f'  {type(r).__name__}: entry={r.entry.start_offset if r.entry else None} blocks={sorted(b.start_offset for b in r.blocks)} type={r.region_type}')

ast_result = generate_ast_from_regions(cfg, regions)
gen = CodeGenerator()
code = gen.generate(ast_result)
print('Decompiled:')
print(code)
os.unlink(tmp)
os.unlink(pyc)
