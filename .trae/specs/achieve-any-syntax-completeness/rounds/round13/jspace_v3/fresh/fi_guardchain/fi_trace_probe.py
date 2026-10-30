# Trace IfRegion creation for entry=18 in fi1.find
import sys, marshal, types
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
import core.cfg.region_analyzer as ra
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion

mc = marshal.loads(open(r'D:\temp\opencode\cl_layout\fi\fi1.pyc','rb').read()[16:])
fnc = [k for k in mc.co_consts if isinstance(k, types.CodeType) and k.co_name=='find'][0]

orig_if = ra.IfRegion.__init__
def traced_if(self, *a, **k):
    orig_if(self, *a, **k)
    e = getattr(self, 'entry', None)
    if e is not None and getattr(e, 'start_offset', None) == 18:
        tb = sorted(getattr(b,'start_offset',None) for b in (self.then_blocks or []))
        eb = sorted(getattr(b,'start_offset',None) for b in (self.else_blocks or []))
        bl = sorted(getattr(b,'start_offset',None) for b in (self.blocks or set()))
        mb = getattr(self, 'merge_block', None)
        import traceback
        st = traceback.extract_stack()[-4:-1]
        caller = ' <- '.join(f'{f.name}:{f.lineno}' for f in reversed(st))
        print(f'[IfRegion@18] then={tb} else={eb} blocks={bl} merge={mb.start_offset if mb else None} via {caller}', file=sys.stderr)
ra.IfRegion.__init__ = traced_if

cfg = build_cfg(fnc, name='find')
an = RegionAnalyzer(cfg, parent_code=fnc)
regions = an.analyze()
