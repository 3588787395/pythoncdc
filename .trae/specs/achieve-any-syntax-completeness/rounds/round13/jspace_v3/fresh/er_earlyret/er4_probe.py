# Probe: region structure for er4 (while True + polarity-inverted guard).
import sys, os
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
os.chdir(r'D:\temp\opencode')

from core.cfg import region_ast_generator as rag

orig = rag.RegionASTGenerator._generate_region

def patched(self, region, *a, **kw):
    r = orig(self, region, *a, **kw)
    t = type(region).__name__
    # er4 f: loop region around offsets 6..90
    try:
        blocks = sorted(getattr(region, 'blocks', []) or [], key=lambda b: b.start_offset)
        spans = [(b.start_offset, b.end_offset) for b in blocks]
    except Exception:
        spans = []
    if any(lo <= 6 <= hi or lo <= 16 <= hi for lo, hi in spans if hi is not None):
        print('[R] %s blocks=%s' % (t, spans), file=sys.stderr)
        import ast as A
        if isinstance(r, list):
            for s in r:
                print('   stmt: %s' % A.dump(s, include_attributes=False)[:400], file=sys.stderr)
        else:
            print('   region-ast: %s' % (type(r).__name__,), file=sys.stderr)
    return r

rag.RegionASTGenerator._generate_region = patched

import importlib.util
spec = importlib.util.spec_from_file_location('pycdc_main', r'F:\Downloads\pythoncdc-main\pycdc.py')
mod = importlib.util.module_from_spec(spec)
sys.modules['pycdc_main'] = mod
spec.loader.exec_module(mod)
out = mod.decompile_pyc('er4_guardappend.pyc')
open('er4_probe_out.py', 'w', encoding='utf-8').write(out)
