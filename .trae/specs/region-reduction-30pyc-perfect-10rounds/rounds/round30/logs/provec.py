# -*- coding: utf-8 -*-
"""Prove mirr_c1c == mirr_c1 except for comment lines (the landing form vs the measured form)."""
import difflib
import io

a = io.open(r'D:/Temp/r30gate/c1/mirr_c1/core/cfg/region_analyzer.py', 'rb').read().decode('utf-8-sig')
b = io.open(r'D:/Temp/r30gate/c1/mirr_c1c/core/cfg/region_analyzer.py', 'rb').read().decode('utf-8-sig')
al, bl = a.split('\r\n'), b.split('\r\n')
print('lines: measured=%d landing=%d delta=%d' % (len(al), len(bl), len(bl) - len(al)))
sm = difflib.SequenceMatcher(None, al, bl, autojunk=False)
ops = [o for o in sm.get_opcodes() if o[0] != 'equal']
assert len(ops) == 1 and ops[0][0] == 'insert', ops
t0, t1 = ops[0][2], ops[0][4]
ins = bl[t0:t1]
assert all(l.strip().startswith('#') for l in ins), ins
print('single insert opcode at line %d, %d lines, all comments: %s' % (t0 + 1, len(ins), ins[0][:34]))
assert al == bl[:t0] + bl[t1:], 'not a pure comment insertion'
print('OK: mirr_c1c minus its %d comment lines == mirr_c1 byte-for-byte' % len(ins))
