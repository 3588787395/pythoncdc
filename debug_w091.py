import sys, os
sys.path.insert(0, r'f:\pythoncdc')
from core.cfg import build_cfg, CFGRegionAnalyzer, IfRegion, WithRegion
import py_compile, tempfile

src = "with ctx1:\n    pass\nwith ctx2:\n    pass"
with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
    f.write(src)
    tmp = f.name
pyc = tmp + 'c'
py_compile.compile(tmp, cfile=pyc, doraise=True)
code_obj = compile(src, tmp, 'exec')
cfg = build_cfg(code_obj)

print('Exception table:')
for e in cfg.exception_table:
    print(f'  start={e.get("start")} end={e.get("end")} target={e.get("target")} depth={e.get("depth")}')

ra = CFGRegionAnalyzer(cfg)
regions = ra.analyze()
print('\nRegions:')
for r in regions:
    print(f'  {type(r).__name__}: entry={r.entry.start_offset if r.entry else None} blocks={sorted(b.start_offset for b in r.blocks)} type={r.region_type}')
    if isinstance(r, WithRegion):
        print(f'    body_offset_start={r.body_offset_start} body_offset_end={r.body_offset_end}')
        print(f'    with_blocks={[b.start_offset for b in r.with_blocks]}')
        print(f'    exception_blocks={[b.start_offset for b in r.exception_blocks]}')
        print(f'    cleanup_blocks={[b.start_offset for b in r.cleanup_blocks]}')

print('\nblock_to_region:')
for block, region in ra.block_to_region.items():
    print(f'  block {block.start_offset} -> {type(region).__name__} entry={region.entry.start_offset if region.entry else None}')

os.unlink(tmp)
os.unlink(pyc)
