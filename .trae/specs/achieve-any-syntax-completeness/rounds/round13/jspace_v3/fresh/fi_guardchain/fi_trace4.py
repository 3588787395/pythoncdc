import sys, marshal, types
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
import core.cfg.region_analyzer as ra
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

mc = marshal.loads(open(r'D:\temp\opencode\cl_layout\fi\fi1.pyc','rb').read()[16:])
fnc = [k for k in mc.co_consts if isinstance(k, types.CodeType) and k.co_name=='find'][0]

def off(b):
    return getattr(b, 'start_offset', None) if b is not None else None

orig_cmfjt = ra.RegionAnalyzer._compute_merge_from_jump_targets
def t_cmfjt(self, header, then_succ, else_succ):
    r = orig_cmfjt(self, header, then_succ, else_succ)
    print(f'[CMFJT] header={off(header)} then={off(then_succ)} else={off(else_succ)} -> {off(r)}', file=sys.stderr)
    return r
ra.RegionAnalyzer._compute_merge_from_jump_targets = t_cmfjt

orig_fncpd = ra.RegionAnalyzer._find_nearest_common_post_dominator
def t_fncpd(self, a, b):
    r = orig_fncpd(self, a, b)
    print(f'[FNCPD] {off(a)},{off(b)} -> {off(r)}', file=sys.stderr)
    return r
ra.RegionAnalyzer._find_nearest_common_post_dominator = t_fncpd

orig_cilm = ra.RegionAnalyzer._compute_in_loop_if_merge
def t_cilm(self, then_succ, else_succ, loop, exclude):
    r = orig_cilm(self, then_succ, else_succ, loop, exclude)
    print(f'[CILM] then={off(then_succ)} else={off(else_succ)} -> {off(r)}', file=sys.stderr)
    return r
ra.RegionAnalyzer._compute_in_loop_if_merge = t_cilm

cfg = build_cfg(fnc, name='find')
an = RegionAnalyzer(cfg, parent_code=fnc)
an.analyze()
