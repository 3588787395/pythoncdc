# -*- coding: utf-8 -*-
"""Round 39 G4-prime: strict-ruler before/after over the ONE changed product.

Compares the committed (pre-landing) OK.py and the landed OK.py for
site-packages/IQCommon/strategy/wizard_quant_api.pyc with the strict ruler,
function by function. Scratch only; nothing in the repo is written.
"""
import importlib.util
import io
import os
import subprocess
import sys

REPO = r'F:\Downloads\pythoncdc-main'
HERE = r'D:\Temp\r39diagA'
REL = 'site-packages/IQCommon/strategy/wizard_quant_api.pyc'
OKREL = 'site-packages/IQCommon/strategy/wizard_quant_apiOK.py'
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')

_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

old = subprocess.check_output(['git', '-C', REPO, 'show', 'HEAD:' + OKREL])
oldp = os.path.join(HERE, 'g4p_old_ok.py')
io.open(oldp, 'w', encoding='utf-8', newline='').write(old.decode('utf-8'))

pyc = os.path.join(REPO, REL.replace('/', os.sep))
A = r10._load_map(pyc)
res = {}
for tag, prod in (('before(HEAD)', oldp), ('after(landed)', os.path.join(REPO, OKREL.replace('/', os.sep)))):
    B = r10._compile_map(prod)
    bad = []
    for k in A:
        if k not in B:
            bad.append((k, 'MISSING'))
            continue
        kind, msg, is_defect = r10.strict_compare(A[k], B[k])
        if is_defect:
            bad.append((k, '%s %s' % (kind, msg)))
    res[tag] = dict(n=len(A), ok=len(A) - len(bad), bad=bad)
    print('%-14s strict ok=%d/%d' % (tag, res[tag]['ok'], res[tag]['n']))
    for k, m in bad:
        print('    %-46s %s' % (k, m))
b = dict(res['before(HEAD)']['bad'])
a = dict(res['after(landed)']['bad'])
print('FIXED  :', sorted(set(b) - set(a)))
print('BROKEN :', sorted(set(a) - set(b)))
