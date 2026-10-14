import re, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
p8 = os.path.join(HERE, '..', 'round8', 'r8v8fixB_repro.py')
src = open(p8, encoding='utf-8-sig').read()
names8 = re.findall(r"^    '([A-Za-z0-9_]+)'", src, re.M)
src9 = open(os.path.join(HERE, 'r9v9_repro.py'), encoding='utf-8-sig').read()
names9 = re.findall(r"^    '([A-Za-z0-9_]+)'", src9, re.M)
core9 = [n for n in names9 if not n.startswith(('r2_', 'r3_', 'r4_', 'r5_', 'r6_', 'r7_', 'r8_', 'n9_'))]
print('round8 PROBES:', len(names8))
print(sorted(names8))
print('round9 core:', len(core9))
print('missing in r9:', sorted(set(names8) - set(core9)))
print('extra in r9:', sorted(set(core9) - set(names8)))
