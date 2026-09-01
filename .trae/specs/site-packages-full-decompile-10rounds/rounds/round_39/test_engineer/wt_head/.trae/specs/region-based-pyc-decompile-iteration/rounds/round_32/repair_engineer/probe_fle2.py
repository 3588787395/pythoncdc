# -*- coding: utf-8 -*-
"""Trace _find_loop_else branch decisions for ptradeAccount order_response_order_update."""
import sys
import marshal
import types

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)
import core.cfg.region_analyzer as ra
from core.cfg import build_cfg

PYC = r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc"


def load_code(p):
    with open(p, "rb") as f:
        f.read(16)
        return marshal.load(f)


def find(co, name):
    if (co.co_name or "<module>") == name:
        return co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r = find(c, name)
            if r:
                return r
    return None


orig = load_code(PYC)
co = find(orig, "order_response_order_update")
cfg = build_cfg(co)

_orig = ra.RegionAnalyzer._find_loop_else


def traced(self, header, loop_body, loop_type, for_iter_exit=None, condition_block=None):
    res = _orig(self, header, loop_body, loop_type, for_iter_exit, condition_block)
    if header.start_offset == 168:
        else_blks, nat = res
        print("header=%d for_iter_exit=%s loop_type=%s" % (
            header.start_offset,
            for_iter_exit.start_offset if for_iter_exit else None,
            loop_type))
        print("  else_blocks=%s natural_exit=%s" % (
            [b.start_offset for b in (else_blks or [])],
            nat.start_offset if nat else None))
        print("  nop_marker=%s" % self._loop_else_nop_marker(for_iter_exit, header))
        # which body blocks have out-of-body successors?
        body_set = set(loop_body) | {header}
        for b in sorted(body_set, key=lambda x: x.start_offset):
            if b == header:
                continue
            for s in b.successors:
                if s not in body_set:
                    bl = b.get_last_instruction()
                    print("  OUT: block %d (last=%s %s) -> %d" % (
                        b.start_offset, bl.opname if bl else "?", bl.argval if bl else "",
                        s.start_offset))
    return res


ra.RegionAnalyzer._find_loop_else = traced

analyzer = ra.RegionAnalyzer(cfg)
analyzer.analyze()
