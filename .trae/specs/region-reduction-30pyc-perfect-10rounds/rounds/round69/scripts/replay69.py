# -*- coding: utf-8 -*-
"""Re-derive the land69 dry-run assertion on the ORIGINAL R68 bytes (the pre-landing
state), so the archive keeps a replay==mirror evidence file after landing already ran.

  git show HEAD:<file>  ->  normalise LF  ->  apply spec edits  ->  re-encode CRLF/BOM
  ->  byte-compare with center/mirr_m69/<file>
"""
import io
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:\Temp\opencode\r69gate\center'
SPECS = [r'D:\Temp\opencode\r69gate\m69_region_analyzer.py.json',
         r'D:\Temp\opencode\r69gate\m69_region_ast_generator.py.json']

for sp in SPECS:
    spec = json.load(io.open(sp, encoding='utf-8'))
    rel = spec['file']
    edits = spec.get('edits') or [{'anchor': spec['anchor'], 'repl': spec['repl']}]
    blob = subprocess.run(['git', 'show', 'HEAD:' + rel], cwd=REPO,
                          capture_output=True).stdout
    bom = blob[:3] == b'\xef\xbb\xbf'
    src = blob[3:].decode('utf-8') if bom else blob.decode('utf-8')
    u = src.replace('\r\n', '\n')
    patched = u
    for k, e in enumerate(edits):
        n = patched.count(e['anchor'])
        assert n == 1, '%s edit %d anchor occurrences=%d' % (rel, k, n)
        patched = patched.replace(e['anchor'], e['repl'])
    ins = sum(e['repl'].count('\n') - e['anchor'].count('\n') for e in edits)
    mir = io.open(os.path.join(ROOT, 'mirr_m69', rel.replace('/', os.sep)), 'rb').read()
    nl = '\r\n' if b'\r\n' in mir else '\n'   # worktree/mirror line ending (blobs are LF)
    out = patched.replace('\n', nl).encode('utf-8')
    if bom:
        out = b'\xef\xbb\xbf' + out
    repo_now = io.open(os.path.join(REPO, rel.replace('/', os.sep)), 'rb').read()
    print('spec %s  file %s  edits %d  inserted lines %d  nl=%s  BOM=%s'
          % (os.path.basename(sp), rel, len(edits), ins,
             'CRLF' if nl == '\r\n' else 'LF', bom))
    print('  replay == measured mirror bytes: %s (%d bytes)'
          % ('OK' if out == mir else 'MISMATCH', len(mir)))
    print('  repository bytes == replay == mirror: %s'
          % ('OK' if repo_now == out == mir else 'MISMATCH'))
    assert out == mir and repo_now == mir
print('land69 replay evidence: PASS (2 files)')
