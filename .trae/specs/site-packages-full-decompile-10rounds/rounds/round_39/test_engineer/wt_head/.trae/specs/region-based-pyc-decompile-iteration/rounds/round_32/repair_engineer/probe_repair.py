# -*- coding: utf-8 -*-
"""修复工程师探针：定位 post-try return 块进入 LoopRegion 的路径。"""
import os
import sys

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

from core.cfg import region_analyzer as ra
from core.cfg.region_ast_generator import RegionASTGenerator

TARGETS = ('f', 'order_response_order_update', 'trade_response_order_update')
_cur = {"n": None}
_og = RegionASTGenerator.generate


def patched_generate(self):
    _cur["n"] = getattr(getattr(self.cfg, 'code', None), 'co_name', None)
    _an = self.region_analyzer
    _orig_analyze = _an.analyze

    def wrapped_analyze():
        result = _orig_analyze()
        if _cur["n"] in TARGETS:
            for r in _an.regions:
                if type(r).__name__ == 'LoopRegion':
                    print("--[%s] LoopRegion entry=%s blocks=%s" % (
                        _cur["n"], r.entry.start_offset,
                        sorted(b.start_offset for b in (r.blocks or []))))
                    print("   else_blocks=%s" % [b.start_offset for b in (r.else_blocks or [])])
                    beb = getattr(r, 'back_edge_block', None)
                    print("   back_edge_block=%s" % (beb.start_offset if beb else None))
                    if beb:
                        print("   be_succs=%s" % [s.start_offset for s in beb.successors])
                    te = [x for x in _an.regions if type(x).__name__ == 'TryExceptRegion']
                    for t in te:
                        print("   TryExcept entry=%s range_blocks=%s" % (
                            t.entry.start_offset,
                            sorted(b.start_offset for b in (t.blocks or []))))
                    # 块 620 附近的 CFG
                    for b in sorted(_an.cfg.blocks, key=lambda x: x.start_offset):
                        if b.start_offset >= 590:
                            li = b.get_last_instruction()
                            print("   blk %-4s last=%-16s succs=%s preds=%s" % (
                                b.start_offset,
                                li.opname if li else '?',
                                [s.start_offset for s in b.successors],
                                [p.start_offset for p in b.predecessors]))
        return result

    self.region_analyzer.analyze = wrapped_analyze
    return _og(self)


RegionASTGenerator.generate = patched_generate

W = os.path.join(ROOT, ".trae", "specs", "region-based-pyc-decompile-iteration",
                 "rounds", "round_32", "test_engineer", "variant_work")
import pycdc
pycdc.decompile_pyc(os.path.join(W, "F_return_after_finally.pyc"), use_cfg=True)
