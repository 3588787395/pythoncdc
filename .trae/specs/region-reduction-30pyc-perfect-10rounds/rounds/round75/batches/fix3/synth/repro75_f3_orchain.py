# -*- coding: utf-8 -*-
# [R75 fix3 synth] 复现：try 内共享尾 + or-is-None 链
def t2(a, b):
    try:
        if a is None or b is None:
            return None
        return a + b
    except Exception:
        return -1
