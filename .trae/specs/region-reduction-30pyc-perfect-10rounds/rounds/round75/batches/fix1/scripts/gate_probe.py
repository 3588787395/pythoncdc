# -*- coding: utf-8 -*-
"""fix1 evidence gate: inspect tool CLIs + locate canary pins."""
import io
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
CEN = r'D:/Temp/opencode/r75gate/center'

for name in ('closeout69.py', 'sstrict67.py', 'adr73.py', 'nhunks.py', 'audit5_g5_67.py'):
    p = os.path.join(CEN, name)
    if not os.path.exists(p):
        print('MISSING', name)
        continue
    L = io.open(p, encoding='utf-8', errors='replace').read().split('\n')
    print('=====', name, len(L))
    for i, l in enumerate(L[:45], 1):
        s = l.strip()
        if s.startswith(('"""', 'usage', 'python', '#')) or 'argv' in s or 'def main' in s:
            print('   ', i, l[:170])

pins = ('3eb76e512df9ab1e', 'af77224b34b203c4', 'e711b8ea86d49a15', '9d09af09249da177')
hits = []
for root, dirs, files in os.walk(r'D:/Temp/opencode/r75gate'):
    dirs[:] = [d for d in dirs if d not in
               ('mirr_jqop1', 'mirr_head', 'mirr_prev', 'build_jqop1', '__pycache__',
                'logs', 'dump')]
    for f in files:
        if not f.endswith(('.py', '.json', '.md', '.txt', '.jsonl')):
            continue
        p = os.path.join(root, f)
        try:
            t = io.open(p, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        for pin in pins:
            if pin in t:
                hits.append((pin, p))
print('=== pin hits')
for pin, p in hits:
    print(' ', pin, p)
