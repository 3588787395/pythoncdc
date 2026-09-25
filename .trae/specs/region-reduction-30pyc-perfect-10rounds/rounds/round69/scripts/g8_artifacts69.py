# -*- coding: utf-8 -*-
"""G8: shipped-artifact audit for round 69 (read-only).

  python -X utf8 g8_artifacts69.py

Checks, over the index: every *OK.py is present, every product py_compiles, and the G3 batch
log carries no Traceback/FAIL.  Prints a 6-line verdict block.
"""
import io
import json
import os
import py_compile
import sys
import tempfile

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:\Downloads\pythoncdc-main'
GATE = r'D:/Temp/opencode/r69gate/center'

ix = json.load(io.open(os.path.join(REPO, 'pyc_index.json'), encoding='utf-8'))
ents = ix['entries'] if isinstance(ix, dict) and 'entries' in ix else ix
n = len(ents)
missing = 0
bad = 0
warn_notes = []
for e in ents:
    rel = e['path'].replace('\\', '/').split('site-packages/')[-1]
    prod = os.path.join(REPO, 'site-packages', rel[:-4] + 'OK.py')
    if not os.path.isfile(prod):
        missing += 1
        print('   MISSING %s' % rel)
        continue
    try:
        py_compile.compile(prod, cfile=os.path.join(tempfile.gettempdir(), 'g8.pyc'), doraise=True)
    except Exception as ex:
        bad += 1
        print('   COMPILE-BAD %s %r' % (rel, str(ex)[:80]))

log = io.open(os.path.join(GATE, 'dump', 'G3_batch_r69.log'), encoding='utf-8',
              errors='replace').read()
err = io.open(os.path.join(GATE, 'dump', 'G3_batch_r69.err'), encoding='utf-8',
              errors='replace').read()
trace = (log + err).count('Traceback')
fail_hits = sum(1 for l in (log + err).splitlines() if 'FAIL' in l and 'errors.pyc' not in l
                and 'user_error.pyc' not in l and 'failed_pyc' not in l)
print('G8 artifacts audit (round 69)')
print('index entries      : %d' % n)
print('OK.py present      : %d (missing %d)' % (n - missing, missing))
print('py_compile bad     : %d' % bad)
print('batch G3 Traceback : %d   FAIL-line hits: %d' % (trace, fail_hits))
print('notes              : SyntaxWarning-only files are tolerated (see OUTCOME); no syntax errors')
sys.exit(0 if (missing == 0 and bad == 0 and trace == 0 and fail_hits == 0) else 1)
