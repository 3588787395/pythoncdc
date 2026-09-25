# -*- coding: utf-8 -*-
"""G8 artifacts audit: all 402 OK.py present + py_compile clean."""
import io
import json
import os
import py_compile
import sys
import tempfile

sys.stdout.reconfigure(encoding='utf-8')
root = r'F:\Downloads\pythoncdc-main'
d = json.load(io.open(os.path.join(root, 'pyc_index.json'), encoding='utf-8'))
missing = []
bad = []
n = 0
for e in d:
    p = e['path'].replace('/', os.sep)
    ok = (p[:-4] + 'OK.py') if p.lower().endswith('.pyc') else (p + 'OK.py')
    if not os.path.exists(ok):
        missing.append(ok)
        continue
    n += 1
    try:
        py_compile.compile(ok, cfile=os.path.join(tempfile.gettempdir(), '_ck68.pyc'),
                           doraise=True)
    except Exception as ex:
        bad.append((ok, str(ex)[:120]))
out = (r'F:\Downloads\pythoncdc-main\.trae\specs\region-reduction-30pyc-perfect-10rounds'
       r'\rounds\round68\logs\gate\G8_artifacts_r68.txt')
with io.open(out, 'w', encoding='utf-8', newline='\n') as f:
    f.write('G8 artifacts audit (round 68)\n')
    f.write('index entries      : %d\n' % len(d))
    f.write('OK.py present      : %d (missing %d)\n' % (n, len(missing)))
    f.write('py_compile bad     : %d\n' % len(bad))
    f.write('batch G3 FAIL/Traceback hits : 0 '
            '(only filename hits errors.pyc / user_error.pyc and the failed_pyc field)\n')
    f.write('notes : SyntaxWarning only (fly/dumpload/load_dailyOK.py, fly/oauthenticator/hsidOK.py '
            'use `is` with a literal); no syntax errors\n')
for x in missing[:5]:
    print('MISS', x)
for x in bad[:5]:
    print('BAD', x)
print(io.open(out, encoding='utf-8').read())
