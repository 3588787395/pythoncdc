#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L3 探针：扫描 core/cfg 内与 slice / BUILD_SLICE / 栈效应模型相关的站点（用于 §2/§6 证据定位）。"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

PATS = [
    ("BUILD_SLICE", re.compile(r"BUILD_SLICE")),
    ("stack_effect", re.compile(r"stack_effect|_stack_delta|needed|pop_count|push_count")),
    ("B148", re.compile(r"\[B148-V3R7\]")),
    ("B151", re.compile(r"\[B151-V3R7\]")),
    ("B150", re.compile(r"\[B150-V3R7\]")),
    ("B152", re.compile(r"\[B152-V3R7\]")),
    ("B145", re.compile(r"\[B145-V3R7\]")),
    ("B139", re.compile(r"\[B139-V3R6\]")),
    ("B140", re.compile(r"\[B140-V3R6\]")),
    ("B153", re.compile(r"\[B153-V3R8\]")),
    ("B157", re.compile(r"\[B157-V3R8\]")),
]


def main():
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "..")
    core = os.path.join(root, "core", "cfg")
    files = [f for f in sorted(os.listdir(core)) if f.endswith(".py")]
    want = sys.argv[1:] if len(sys.argv) > 1 else ["BUILD_SLICE"]
    for fn in files:
        p = os.path.join(core, fn)
        for i, line in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
            for name, pat in PATS:
                if name in want and pat.search(line):
                    print("%s:%d %s | %s" % (fn, i, name, line.rstrip()[:190]))
                    break


if __name__ == "__main__":
    main()
