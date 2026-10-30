# Trace generator region dispatch for m3 (minimal, no cwd change)
import sys, importlib.util
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')

import core.cfg.region_ast_generator as rag

orig_gr = rag.RegionASTGenerator._generate_region
def gr(self, region, *a, **k):
    rt = type(region).__name__
    bl = []
    try:
        bl = sorted(getattr(b, 'start_offset', None) for b in (getattr(region, 'blocks', None) or []))
    except TypeError:
        bl = ['?']
    ent = getattr(getattr(region, 'entry', None), 'start_offset', '?')
    print(f'[GEN] {rt}@{ent} blocks={bl}', file=sys.stderr)
    return orig_gr(self, region, *a, **k)
rag.RegionASTGenerator._generate_region = gr

spec = importlib.util.spec_from_file_location('pycdc_main', r'F:\Downloads\pythoncdc-main\pycdc.py')
mod = importlib.util.module_from_spec(spec)
sys.modules['pycdc_main'] = mod
spec.loader.exec_module(mod)
out = mod.decompile_pyc(r'D:\temp\opencode\cl_layout\fe\m3.pyc')
print('==== product ====')
print(out)
