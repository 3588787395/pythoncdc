import sys, os
sys.path.insert(0, r'f:\pythoncdc')
from core.cfg import build_cfg, CFGRegionAnalyzer, WithRegion, IfRegion, LoopRegion
from core.cfg.region_ast_generator import generate_ast_from_regions
from core.cfg.code_generator import CodeGenerator
import py_compile, tempfile

src = "with ctx:\n    while x < 3:\n        x += 1"
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
    if isinstance(r, WithRegion):
        print(f'    body_start={r.body_offset_start} body_end={r.body_offset_end}')
        print(f'    with_blocks={[b.start_offset for b in r.with_blocks]}')
    if isinstance(r, LoopRegion):
        print(f'    header={r.header_block.start_offset if r.header_block else None} body={[b.start_offset for b in r.body_blocks]}')

ast_result = generate_ast_from_regions(cfg, regions)
gen = CodeGenerator()
code = gen.generate(ast_result)
print('\nDecompiled:')
print(code)
os.unlink(tmp)
os.unlink(pyc)
