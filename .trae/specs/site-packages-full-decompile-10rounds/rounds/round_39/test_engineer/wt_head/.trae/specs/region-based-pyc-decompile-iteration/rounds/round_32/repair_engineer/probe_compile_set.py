# -*- coding: utf-8 -*-
"""验证 CPython 3.11 对集合比较的字节码形态（决定渲染策略）。
用法：D:/Python/python.exe probe_compile_set.py
"""
import dis


def f1(status):
    if status in {5, 6}:
        return 1
    return 0


def f2(status):
    if status in frozenset({5, 6}):
        return 1
    return 0


print("=== f1: status in {5, 6} ===")
dis.dis(f1)
print("f1 consts:", f1.__code__.co_consts)
print()
print("=== f2: status in frozenset({5, 6}) ===")
dis.dis(f2)
print("f2 consts:", f2.__code__.co_consts)
