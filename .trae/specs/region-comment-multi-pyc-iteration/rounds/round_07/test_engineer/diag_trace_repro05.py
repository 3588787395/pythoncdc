"""Trace repro_05: print all regions + trace handler_entry consumption."""
import sys, os, marshal, types, traceback, py_compile, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
for _ in range(8):
    if os.path.exists(os.path.join(sys.path[0], 'pycdc.py')):
        break
    sys.path[0] = os.path.dirname(sys.path[0])

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import TryExceptRegion, WithRegion, IfRegion

SRC = r'f:\Downloads\pythoncdc-main\.trae\specs\region-comment-multi-pyc-iteration\rounds\round_07\test_engineer\minimal_repros\repro_05_pattern_t_with_then_try_except.py'
d = tempfile.mkdtemp()
pyp = os.path.join(d, 'r05.pyc')
py_compile.compile(SRC, pyp, doraise=True, quiet=2)
with open(pyp, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find(co, name):
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            if c.co_name == name:
                return c
            r = find(c, name)
            if r:
                return r
    return None

fn = find(code, 'build')
cfg = build_cfg(fn, 'build')
gen = RegionASTGenerator(cfg)

print('=== ALL REGIONS ===')
for _r in gen.regions:
    t = type(_r).__name__
    entry = getattr(_r, 'entry', None)
    eoff = entry.start_offset if entry is not None else None
    blks = sorted(b.start_offset for b in getattr(_r, 'blocks', []))
    extra = ''
    if isinstance(_r, TryExceptRegion):
        heb = sorted(b.start_offset for b in _r.handler_entry_blocks)
        extra = ' handler_entries=%s' % heb
    print('  %s entry=%s blocks=%s%s' % (t, eoff, blks, extra))

print('\n=== block_to_region owners ===')
for _b, _r in sorted(gen.region_analyzer.block_to_region.items(), key=lambda x: x[0].start_offset):
    print('  block %d -> %s' % (_b.start_offset, type(_r).__name__))

# Collect handler_entry offsets across all TryExceptRegions
target_offs = set()
for _r in gen.regions:
    if isinstance(_r, TryExceptRegion):
        for _heb in _r.handler_entry_blocks:
            target_offs.add(_heb.start_offset)
print('\nhandler_entry offsets:', sorted(target_offs))


class LoggingSet(set):
    def __init__(self, label, *a, **kw):
        super().__init__(*a, **kw)
        self._label = label
    def add(self, x):
        off = getattr(x, 'start_offset', None)
        if off in target_offs and x not in self:
            print('\n*** %s.add(block %d) ***' % (self._label, off))
            st = traceback.extract_stack()
            for fr in st[2:-1]:
                print('    %s:%d in %s' % (os.path.basename(fr.filename), fr.lineno, fr.name))
        super().add(x)
    def update(self, others):
        for x in others:
            self.add(x)


gen.generated_blocks = LoggingSet('generated_blocks', gen.generated_blocks)
try:
    gen.generate()
    print('\n[generate completed]')
except Exception:
    traceback.print_exc()
