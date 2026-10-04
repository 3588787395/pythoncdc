# Source Generated with Decompyle++ (Python version)
# File: r10_01_import_alias.pyc (Python 3.11)

__doc__ = 'r10_01: import / dotted-name / alias 基础形态（表A Import/ImportFrom/Alias 行）'
import a.b.c
import x.y as q
import json as j
import os as o
def imp_dotted(v):
    if v > 0:
        return a.b.c.attr(v)
    else:
        for i in range(3):
            if i % 2:
                a.b.c.touch(i)
def imp_alias_multi(vals):
    out = []
    for v in vals:
        if v > 1:
            out.append(j.dumps(v))
            continue
        out.append(o.getcwd())
        continue
    return q.join(out) if out else None
def imp_dotted_alias(n):
    while n > 0:
        if n % 3 == 0:
            try:
                return x.y.helper(n)
            except ValueError:
                n -= 1
        n -= 1
    return None
