# -*- coding: utf-8 -*-
"""flip_time.py -- chronological claim/free timeline for @7972..@8588, with deciding lines.

usage: python -X utf8 flip_time.py
"""
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace',
                              line_buffering=True)
M = 'D:/Temp/r110/'
GEN = open(M + 'core/cfg/region_ast_generator.py', encoding='utf-8-sig',
           errors='replace').read().replace('\r\n', '\n').split('\n')
frames = json.load(open(M + 'logs/lines_r110.json'))


def src(n):
    try:
        return (GEN[n - 1].strip() if n else '?')[:104]
    except Exception:
        return '?'


ev = []
for f in frames:
    for (prev, seen, o, kind) in f.get('flips', []):
        ev.append((f['seq'], f['fn'], f['reg'], o, kind, prev, seen, f['nblk_arg']))
ev.sort()

print('=== chronological generated_blocks transitions (executed_line -> observed_line) ===')
print('frame_seq = the census seq of THIS traced call; nblk = len(blocks) arg')
for row in ev:
    seq, fn, reg, o, kind, prev, seen, nblk = row
    print('@%-5s %-4s seq=%-4s %-22s reg=%-22s nblk=%-5s executed=%-6s %-52s || next=%-6s %s'
          % (o, kind, seq, fn, reg, nblk, prev, src(prev), seen, src(seen)))

print()
print('=== FIRST transition per offset ===')
first = {}
for row in ev:
    first.setdefault(row[3], row)
for o in sorted(first):
    seq, fn, reg, _, kind, prev, seen, nblk = first[o]
    print('@%-5s first=%-3s in seq=%-4s %-22s reg=%-22s line %s: %s'
          % (o, kind, seq, fn, reg, prev, src(prev)))
