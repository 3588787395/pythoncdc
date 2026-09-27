# -*- coding: utf-8 -*-
"""run_synth.py <arm> <pyc> ...  -- decompile with an existing mirror arm and run the
mandated ruler, printing one line per pyc.  Products land under center/build_<arm>/."""
import hashlib
import io
import json
import os
import subprocess
import sys

REPO = r'F:\Downloads\pythoncdc-main'
GATE = r'D:/Temp/opencode/r73gate/center'
sys.stdout.reconfigure(encoding='utf-8')

ARM = sys.argv[1]
PYCS = sys.argv[2:]
sys.path.insert(0, GATE)
import h62  # noqa: E402

pycdc = h62._load_arm(ARM)
if not os.path.isdir(GATE + '/build_' + ARM):
    os.makedirs(GATE + '/build_' + ARM)
_s = __import__('importlib.util', fromlist=['spec_from_file_location']).spec_from_file_location(
    'pbv', os.path.join(REPO, 'scripts', 'pyc_batch_verify.py'))
pbv = __import__('importlib.util', fromlist=['module_from_spec']).module_from_spec(_s)
_s.loader.exec_module(pbv)

for p in PYCS:
    rel = p.replace('\\', '/')
    r0 = REPO.replace('\\', '/') + '/site-packages/'
    if rel.startswith(r0):
        rel = rel[len(r0):]
    dst = os.path.join(GATE + '/build_' + ARM,
                       rel.replace('/', '__')[:-4].replace(':', '_') + 'OK.py').replace('\\', '/')
    text = pycdc.decompile_pyc(p)
    io.open(dst, 'w', encoding='utf-8', newline='\n').write(text)
    r = pbv.bytecode_diff(p, dst)
    v = subprocess.run([sys.executable, '-X', 'utf8',
                        os.path.join(REPO, 'scripts', 'pyc_verify.py'),
                        'single', p, '--source', dst],
                       capture_output=True, text=True, encoding='utf-8',
                       errors='replace', timeout=280)
    out = (v.stdout or '') + (v.stderr or '')
    st = [l.strip() for l in out.splitlines() if l.strip().startswith('[single] status=')]
    print('%-6s %-46s sha16=%s official=%s/%s mism=%s' % (
        ARM, os.path.basename(p),
        hashlib.sha256(text.encode('utf-8')).hexdigest()[:16],
        r.get('matched_functions'), r.get('total_functions'),
        [[m.get('name'), m.get('orig_count'), m.get('decomp_count'),
          m.get('jump_diffs'), m.get('true_diffs')] for m in (r.get('mismatches') or [])]))
    for l in out.splitlines():
        if 'Failure' in l or 'status=' in l:
            print('        ' + l.strip())
