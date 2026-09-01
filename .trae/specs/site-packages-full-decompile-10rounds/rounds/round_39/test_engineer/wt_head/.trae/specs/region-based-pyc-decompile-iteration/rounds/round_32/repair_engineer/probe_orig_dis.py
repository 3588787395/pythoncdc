# -*- coding: utf-8 -*-
"""Dump full orig disassembly + exception table for the two functions."""
import os
import sys
import marshal
import types
import dis

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
for name in ("order_response_order_update", "trade_response_order_update"):
    co = find(orig, name)
    print("=" * 90)
    print("FUNC", name)
    dis.dis(co)
    print("--- exception table ---")
    if hasattr(co, "co_exceptiontable"):
        # parse manually: (start, end, target, depth) as in 3.11
        t = co.co_exceptiontable
        i = 0
        while i < len(t):
            b0 = t[i]
            b1 = t[i + 1]
            b2 = t[i + 2]
            start = b0 | ((b1 & 0x7F) << 8)
            length = b1 >> 7 | (b2 & 0x7F) << 1
            b3 = t[i + 3]
            target = b2 >> 7 | (b3 & 0x7F) << 1
            b4 = t[i + 4]
            b5 = t[i + 5]
            depth = b3 >> 7 | (b4 << 1) | ((b5 & 0x7F) << 9)
            print("  %d to %d -> %d (depth %d)" % (start, start + length, target, depth))
            i += 6
