# -*- coding: utf-8 -*-
"""Compile minimal try/finally+for shapes and dump tails to find which source
produces the original ptradeAccount tail layout:
    [finally-copy] JUMP_FORWARD → [handler] → LOAD_CONST None; RETURN_VALUE
"""


def shape_a(algo, datalist):
    # for-else + finally, no explicit return
    try:
        for item in datalist:
            x = item
        else:
            algo.set_instance()
    finally:
        algo.release()


def shape_b(algo, datalist):
    # loop then statement (not else) + finally, no explicit return
    try:
        for item in datalist:
            x = item
        algo.set_instance()
    finally:
        algo.release()


def shape_c(algo, datalist):
    # loop then statement (not else) + finally + explicit return None
    try:
        for item in datalist:
            x = item
        algo.set_instance()
    finally:
        algo.release()
    return None


def shape_d(algo, datalist):
    # for-else + finally + explicit return None
    try:
        for item in datalist:
            x = item
        else:
            algo.set_instance()
    finally:
        algo.release()
    return None


if __name__ == "__main__":
    import dis
    import sys

    for fn in (shape_a, shape_b, shape_c, shape_d):
        co = fn.__code__
        print("=" * 70)
        print(fn.__name__)
        dis.dis(co)
        t = co.co_exceptiontable
        i = 0
        print("--- exception table ---")
        while i + 6 <= len(t):
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
