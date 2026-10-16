#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9.2 续作 B126 深度诊断（只读 monkeypatch，无 core 文件改动）。

用法: python r9v9fix3_diag_b126.py <pyc> [func_name]
输出: stdout（块表 / 回边目标 / 区域表 / assert 细节）。
"""
import marshal
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)

from core.cfg import build_cfg  # noqa: E402
from core.cfg.region_analyzer import (  # noqa: E402
    RegionAnalyzer, AssertRegion, LoopRegion, IfRegion)


def find_code(code, name):
    for c in code.co_consts:
        if hasattr(c, 'co_name'):
            if c.co_name == name:
                return c
            r = find_code(c, name)
            if r is not None:
                return r
    return None


def dump_cfg(cfg):
    print('== blocks ==')
    back_targets = set()
    for b in cfg.get_blocks_in_order():
        for p in b.predecessors:
            if p.start_offset >= b.start_offset:
                back_targets.add(b.start_offset)
    for b in cfg.get_blocks_in_order():
        last = b.get_last_instruction()
        succs = sorted(s.start_offset for s in b.successors)
        preds = sorted(p.start_offset for p in b.predecessors)
        cond = sorted(s.start_offset for s in b.conditional_successors)
        print('[CFG] blk@%-4s last=%-30s arg=%-6s succ=%-16s pred=%-16s cond=%s'
              % (b.start_offset, last.opname if last else None,
                 getattr(last, 'argval', None) if last else None,
                 succs, preds, cond))
    print('== back-edge targets (pred.off >= blk.off) ==', sorted(back_targets))
    return back_targets


def main():
    pyc = sys.argv[1]
    func = sys.argv[2] if len(sys.argv) > 2 else 'assert_deep'
    raw = marshal.loads(open(pyc, 'rb').read()[16:])
    code = raw if raw.co_name == func else find_code(raw, func)
    assert code is not None, 'func %s not found' % func
    cfg = build_cfg(code)
    back_targets = dump_cfg(cfg)

    orig_analyze = RegionAnalyzer.analyze

    def analyze2(self):
        res = orig_analyze(self)
        print('== regions (%d) ==' % len(self.regions))
        for r in self.regions:
            blocks = sorted(b.start_offset for b in (r.blocks or set()))
            entry = getattr(r, 'entry', None)
            print('[REG] %-22s entry=%-4s blocks=%s'
                  % (type(r).__name__,
                     entry.start_offset if entry else None, blocks))
        for r in self.regions:
            if isinstance(r, AssertRegion):
                cb = r.condition_block
                mb = r.message_block
                print('[ASSERT] entry=%s cond=%s msg=%s chain=%s ops=%s '
                      'boolop=%s boolops=%s parent=%s'
                      % (r.entry.start_offset if r.entry else None,
                         cb.start_offset if cb else None,
                         mb.start_offset if mb else None,
                         [b.start_offset for b in r.chained_compare_blocks or []],
                         r.chained_compare_ops,
                         [b.start_offset for b in r.boolop_chain_blocks or []],
                         r.boolop_chain_ops,
                         type(r.parent).__name__ if r.parent else None))
                for b in sorted(r.blocks or set(), key=lambda x: x.start_offset):
                    print('    [A.blk@%s] %s' % (
                        b.start_offset,
                        ' ; '.join(i.opname for i in b.instructions)))
        for r in self.regions:
            if isinstance(r, LoopRegion) or type(r).__name__ == 'WhileRegion':
                print('[LOOP] %-18s entry=%s blocks=%s cond=%s'
                      % (type(r).__name__,
                         r.entry.start_offset if r.entry else None,
                         sorted(b.start_offset for b in (r.blocks or set())),
                         getattr(getattr(r, 'condition_block', None),
                                 'start_offset', None)))
        return res

    RegionAnalyzer.analyze = analyze2
    az = RegionAnalyzer(cfg)
    az.analyze()
    print('-> done (back targets=%s)' % sorted(back_targets))


if __name__ == '__main__':
    main()
