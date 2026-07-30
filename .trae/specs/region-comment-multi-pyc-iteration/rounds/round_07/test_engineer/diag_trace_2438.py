"""Diagnostic: find WHO adds block 2438 (handler entry of try@2394) to
generated_blocks before _generate_try is called.

Replaces gen.generated_blocks with a LoggingSet that prints a stack trace when
a block with start_offset==2438 is added.
"""
import sys, os, marshal, types, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
for _ in range(8):
    if os.path.exists(os.path.join(sys.path[0], 'pycdc.py')):
        break
    sys.path[0] = os.path.dirname(sys.path[0])

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import TryExceptRegion

TARGET_OFF = 2438

class LoggingSet(set):
    def __init__(self, label, *a, **kw):
        super().__init__(*a, **kw)
        self._label = label
    def add(self, x):
        off = getattr(x, 'start_offset', None)
        if off == TARGET_OFF and x not in self:
            print('\n*** %s.add(block %d) ***' % (self._label, off))
            # print compact stack (skip this frame + logging internals)
            st = traceback.extract_stack()
            for fr in st[2:-1]:
                print('    %s:%d in %s' % (os.path.basename(fr.filename), fr.lineno, fr.name))
        super().add(x)
    def update(self, others):
        for x in others:
            self.add(x)


_orig = RegionASTGenerator._generate_try
def traced(self, region):
    if isinstance(region, TryExceptRegion) and region.try_offset_start == 2394:
        print('\n=== _generate_try ENTER try@2394; 2438 in generated_blocks=%s ==='
              % (any(getattr(b,'start_offset',None)==TARGET_OFF for b in self.generated_blocks),))
    return _orig(self, region)
RegionASTGenerator._generate_try = traced

PYC = r"F:\Downloads\pythoncdc-main\site-packages\IQCommon\backtest\backtest.pyc"
with open(PYC, 'rb') as f:
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

fn = find(code, 'handle_backtest_build')
cfg = build_cfg(fn, 'handle_backtest_build')
gen = RegionASTGenerator(cfg)
# replace generated_blocks with logging set
gen.generated_blocks = LoggingSet('generated_blocks', gen.generated_blocks)
try:
    ast_dict = gen.generate()
    print('\n[generate completed]')
except Exception:
    traceback.print_exc()
