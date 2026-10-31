import sys, marshal, types
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
import core.cfg.region_analyzer as ra
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

mc = marshal.loads(open(r'D:\temp\opencode\cl_layout\fi\fi1.pyc','rb').read()[16:])
fnc = [k for k in mc.co_consts if isinstance(k, types.CodeType) and k.co_name=='find'][0]

orig = ra.RegionAnalyzer._build_basic_if_region
def traced(self, block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block, **k):
    if block is not None and getattr(block, 'start_offset', None) == 18:
        tb = sorted(getattr(b,'start_offset',None) for b in (then_blocks or []))
        eb = sorted(getattr(b,'start_offset',None) for b in (else_blocks or []))
        m = getattr(merge, 'start_offset', None) if merge is not None else None
        print(f'[build_basic_if_region] block=18 then={tb} else={eb} merge={m}', file=sys.stderr)
    return orig(self, block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block, **k)
ra.RegionAnalyzer._build_basic_if_region = traced

orig_elif = ra.RegionAnalyzer._build_elif_region
def traced_elif(self, block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block, **k):
    if block is not None and getattr(block, 'start_offset', None) == 18:
        tb = sorted(getattr(b,'start_offset',None) for b in (then_blocks or []))
        eb = sorted(getattr(b,'start_offset',None) for b in (else_blocks or []))
        m = getattr(merge, 'start_offset', None) if merge is not None else None
        r = traced_elif_orig(self, block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block, **k)
        print(f'[build_elif_region] block=18 then={tb} else={eb} merge={m} -> {type(r).__name__ if r else None}', file=sys.stderr)
        return r
    return traced_elif_orig(self, block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block, **k)
traced_elif_orig = ra.RegionAnalyzer._build_elif_region
ra.RegionAnalyzer._build_elif_region = traced_elif

cfg = build_cfg(fnc, name='find')
an = RegionAnalyzer(cfg, parent_code=fnc)
an.analyze()
