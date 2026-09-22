# -*- coding: utf-8 -*-
"""Round 37: pin the G0 witness set into test_repros so future rounds' G2' battery carries it.

  python -X utf8 pinbat37.py

Copies <scratch>/<bat>/<stem>.py into the repo battery dir under an r37_NN_ prefix and
re-py_compiles it there (explicit cfile, so co_filename matches the pinned source path).
Asserts the copy set has exactly the expected size and that every product compiles.
"""
import io
import os
import py_compile
import shutil
import sys

REPO = r'F:\Downloads\pythoncdc-main'
SRC = r'D:/Temp/r37gate/r37'
OWN = r'D:/Temp/r37diagA'          # line A's private dir: its ladder cases were re-measured here,
                                   # on the orchestrator's own mirrors, but the sources are authored there.
DST = os.path.join(REPO, 'test_repros', 'round37_ancestor_elif_or_arm')

# (root, bat, stem, pinned name)
CASES = [
    (OWN, 'ladder', 'l2_nested_orarm', 'witness_or_arm_in_ancestor_elif_chain'),
    (OWN, 'ladder2', 'n6_orarm_else_sibling', 'witness_or_arm_with_else_sibling'),
    (OWN, 'ladder2', 'n8_orarm_then_plain_arm', 'witness_or_arm_with_plain_then_sibling'),
    (SRC, 'wit', 'c4_loop_ancestor_single_arm', 'witness_loop_ancestor_single_arm_chain'),
    (OWN, 'ladder', 'l0b_plain_elif_tail', 'control_plain_elif_tail'),
    (OWN, 'ladder', 'l1_nested_chain_in_first_arm', 'control_nested_chain_in_first_arm'),
    (OWN, 'ladder', 'm1_orarm_plain_sibling', 'control_orarm_plain_sibling'),
    (OWN, 'ladder2', 'n7_plain_or_arms', 'control_plain_or_arms'),
]

assert len(CASES) == 8
os.makedirs(DST, exist_ok=True)
made = []
for root, bat, stem, name in CASES:
    s = os.path.join(root, bat, stem + '.py')
    if not os.path.isfile(s):
        raise SystemExit('missing source %s' % s)
    tag = 'r37_%s' % name
    py = os.path.join(DST, tag + '.py')
    pyc = os.path.join(DST, tag + '.pyc')
    io.open(py, 'w', encoding='utf-8', newline='\n').write(
        io.open(s, encoding='utf-8').read())
    py_compile.compile(py, cfile=pyc, doraise=True)
    made.append((tag, os.path.getsize(py), os.path.getsize(pyc)))

for i, m in enumerate(sorted(made), 1):
    print('r37_%02d %-56s py=%5d pyc=%6d' % (i, m[0], m[1], m[2]))
print('dir %s  files %d' % (DST, len([f for f in os.listdir(DST) if f.endswith(('.py', '.pyc'))])))
