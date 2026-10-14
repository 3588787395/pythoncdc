"""Coverage audit: does every .pyc under site-packages have a same-directory <name>OK.py product?

The 402-file gate is the verification face, but the objective is stated per-pyc, so this walks the
whole tree and reports the gaps explicitly instead of inferring them from the gate.

usage: python -X utf8 coverage_audit.py
"""
import collections
import os

SEP = chr(92)
root = os.path.abspath('site-packages')
pyc, ok, errs = [], [], []
for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: errs.append(str(e))):
    for f in filenames:
        p = os.path.join(dirpath, f)
        if f.endswith('.pyc'):
            pyc.append(p)
        elif f.endswith('OK.py'):
            ok.append(p)
okset = set(ok)
pycset = set(pyc)
missing = [p for p in pyc if p[:-4] + 'OK.py' not in okset]
orphans = [p for p in ok if p[:-len('OK.py')] + '.pyc' not in pycset]
print('walk errors: %d' % len(errs))
print('pyc=%d  OK.py=%d' % (len(pyc), len(ok)))
print('pyc WITHOUT adjacent OK.py: %d' % len(missing))
grp = collections.Counter()
magic = collections.Counter()
for p in missing:
    rel = os.path.relpath(p, root).replace(SEP, '/')
    grp[rel.split('/')[0]] += 1
    try:
        magic['0x%08x' % int.from_bytes(open(p, 'rb').read(4), 'little')] += 1
    except Exception:
        magic['unreadable'] += 1
print('missing grouped by top dir: %s' % dict(grp))
print('missing pyc magic values: %s' % dict(magic))
print('sample missing (18):')
for p in missing[:18]:
    print('   ', os.path.relpath(p, root).replace(SEP, '/'))
print('OK.py with no .pyc partner: %d' % len(orphans))
for p in orphans[:8]:
    print('   ', os.path.relpath(p, root).replace(SEP, '/'))
