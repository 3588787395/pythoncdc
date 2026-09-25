# -*- coding: utf-8 -*-
"""diag2 R66: line-hit probe on the LANDED core (read-only; writes only into workspace).

usage: python -X utf8 probe_lines.py <pyc> <lo-hi,lo-hi,...> <out.py>
Counts executed source lines inside core/cfg/region_ast_generator.py within the
given line ranges, tagged with the enclosing method name.
"""
import collections
import io
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')
import pycdc  # noqa

GEN_ABS = os.path.abspath(os.path.join(REPO, 'core', 'cfg', 'region_ast_generator.py'))
RANGES = []
for spec in sys.argv[2].split(','):
    a, b = spec.split('-')
    RANGES.append((int(a), int(b)))

hits = collections.Counter()


def inr(ln):
    return any(a <= ln <= b for a, b in RANGES)


def trace(frame, event, arg):
    if event == 'line' and frame.f_code.co_filename and \
            os.path.abspath(frame.f_code.co_filename) == GEN_ABS and inr(frame.f_lineno):
        hits[(frame.f_code.co_name, frame.f_lineno)] += 1
    return trace


sys.settrace(trace)
try:
    text = pycdc.decompile_pyc(sys.argv[1])
finally:
    sys.settrace(None)
io.open(sys.argv[3], 'w', encoding='utf-8').write(text)
print('=== hits (%s) ranges=%s' % (os.path.basename(sys.argv[1]), RANGES))
for (fn, ln), n in sorted(hits.items(), key=lambda kv: kv[0][1]):
    print('  %-46s L%-6d x%d' % (fn, ln, n))
