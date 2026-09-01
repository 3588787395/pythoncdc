# -*- coding: utf-8 -*-
"""Round 04 G1 复现: 普通 yield 语句丢失。"""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import decompile

CASES = [
    ("P1 while True yield 首", "def f(start=1):\n    i = start\n    while True:\n        yield i\n        i += 1\n"),
    ("P2 while True yield 尾", "def f():\n    while True:\n        i = 1\n        yield i\n"),
    ("P3 for 循环 yield", "def f(items):\n    for x in items:\n        yield x\n"),
    ("P4 for 循环 yield+处理", "def f(items):\n    for x in items:\n        y = x * 2\n        yield y\n"),
    ("P5 yield if 分支", "def f(n):\n    if n > 0:\n        yield n\n    else:\n        yield 0\n"),
    ("P6 多 yield while", "def f():\n    i = 0\n    while i < 10:\n        i += 1\n        yield i\n        yield i * 2\n"),
    ("P7 yield 表达式赋值", "def f():\n    while True:\n        got = yield 1\n        if got:\n            break\n"),
    ("P8 yield from 对照", "def f(items):\n    yield from items\n"),
]

for name, src in CASES:
    try:
        out = decompile(src, "<g1>")
        ok = "yield" in out
        print(f"[{'OK ' if ok else 'BAD'}] {name}")
        if not ok:
            print("---- 反编译输出 ----")
            for line in out.splitlines():
                print("   ", line)
    except Exception as e:
        print(f"[ERR] {name}: {type(e).__name__}: {e}")
