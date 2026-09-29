# -*- coding: utf-8 -*-
"""fix1 jq: build spec jqop1.json -- restore the condition operand that
_cjb_skip_inline_if drops (jq_trans_module 63/65 -> 65/65 target)."""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:\Downloads\pythoncdc-main'
CORE = REPO + r'\core\cfg\region_ast_generator.py'
OUT = r'D:/Temp/opencode/r75gate/fix1/specs/jqop1.json'

raw = io.open(CORE, 'rb').read()
src = raw.decode('utf-8-sig').replace('\r\n', '\n')
lines = src.split('\n')


def block(a, b):
    return '\n'.join(lines[a - 1:b])


a1 = block(47629, 47633)
a2 = block(47639, 47643)
a3 = block(32662, 32662)
print('--- anchor1 ---')
print(a1)
print('--- anchor2 ---')
print(a2)
print('--- anchor3 ---')
print(a3)
for name, a in (('a1', a1), ('a2', a2), ('a3', a3)):
    print('%s count=%d' % (name, src.count(a)))
