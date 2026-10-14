"""R21-44 2x2 generator-half probe: after analyze(), force the compound-while BoolOpRegion
to survive (attach as child of the hdr=704 loop + re-own operand blocks 232/364/522/544),
then generate broker and judge. This isolates whether the GENERATOR can rebuild
`Or([A, B, And([C, D])])` for _sync_worker once the analyzer hands it a surviving region.
"""
import marshal, os, sys
sys.path.insert(0, r"D:/Temp/r71")
import core.cfg.region_analyzer as RA
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, BoolOpRegion

_orig = RegionAnalyzer._detect_while_condition_boolop_chain
_made = {}
def patched(self, cb, loop):
    r = _orig(self, cb, loop)
    if r and len(r) >= 2:
        return r
    if getattr(cb, 'start_offset', None) == 232 and getattr(getattr(loop, 'header_block', None), 'start_offset', None) == 704:
        b = [self.cfg.get_block_by_offset(o) for o in (232, 364, 522, 544)]
        _made['chain'] = [(b[0], 'or'), (b[1], 'or'), (b[2], 'and'), (b[3], 'and')]
        return _made['chain']
    return r
RegionAnalyzer._detect_while_condition_boolop_chain = patched

_reate = RA.RegionAnalyzer._create_boolop_region_from_chain
def ctrace(self, chain, claimed):
    reg = _reate(self, chain, claimed)
    if reg and chain and chain[0][0].start_offset == 232:
        _made['region'] = reg
    return reg
RegionAnalyzer._create_boolop_region_from_chain = ctrace

import core.cfg.region_ast_generator as GAG
# wrap analyze() to re-attach after the clear/rebuild
_oan = RegionAnalyzer.analyze
def analyze2(self):
    regions = _oan(self)
    reg = _made.get('region')
    if reg is not None:
        host = next((r for r in regions if isinstance(r, LoopRegion)
                     and getattr(r.header_block, 'start_offset', None) == 704
                     and getattr(r.condition_block, 'start_offset', None) == 232), None)
        if host is not None:
            if reg not in regions:
                regions.append(reg)
            reg.parent = host
            host.children.append(reg)
            for b in reg.blocks:
                self.block_to_region[b] = reg
            self.regions.append(reg) if reg not in self.regions else None
            print('[FORCE] attached boolop entry@232 as child of while@704; btr232=', type(self.block_to_region.get(self.cfg.get_block_by_offset(232))).__name__)
    return regions
RegionAnalyzer.analyze = analyze2

import pycdc
PYC = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc'
out = 'D:/Temp/r71/prod/broker_forced.py'
sys.argv = ['pycdc.py', '--region', '-o', out, PYC]
try:
    pycdc.main()
except SystemExit:
    pass
print('WROTE', out, os.path.exists(out))
