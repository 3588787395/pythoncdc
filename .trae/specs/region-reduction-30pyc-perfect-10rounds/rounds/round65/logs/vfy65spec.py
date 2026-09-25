# -*- coding: utf-8 -*-
"""Center-side generic spec verifier: does this spec apply cleanly to the LANDED bytes?

  python -X utf8 vfy65spec.py <spec.json> [<spec2.json> ...]

Read-only over the repo (writes nothing, runs no decompiler). For each spec reports the
target file, edit count, chained anchor uniqueness, net line delta, resulting
bytes/sha/hygiene, py_compile+ast verdict, and the list of `[R..]` markers that moved.
"""
import ast
import hashlib
import io
import json
import os
import py_compile
import sys
import tempfile

sys.stdout.reconfigure(encoding='utf-8')
CR = chr(13)
BS = os.sep
REPO = r'F:/Downloads/pythoncdc-main'
MARKS = ['[R64-b2]', '[R64-B2]', '[R64-D4-B]', '[R64-B1 sibling', '[R64-D4-A]',
         '[R64-diag1 closed-shared-exit-prefix]', '[R65-D5-A]', '[R65-D5-B]']


def load(rel):
    raw = io.open(os.path.join(REPO, rel.replace('/', BS)), 'rb').read()
    bom = raw[:3] == b'\xef\xbb\xbf'
    text = raw.decode('utf-8-sig')
    nl = '\r\n' if text.count(CR) else '\n'
    return raw, bom, nl, text.replace('\r\n', '\n')


def markers(text):
    lines = text.split('\n')
    return {m: [i + 1 for i, l in enumerate(lines) if m in l] for m in MARKS}


def check(path):
    spec = json.load(io.open(path, encoding='utf-8'))
    rel = spec['file']
    edits = spec.get('edits') or [{'anchor': spec['anchor'], 'repl': spec['repl']}]
    raw, bom, nl, u = load(rel)
    before = markers(u)
    print('== %s' % os.path.basename(path))
    print('   file=%s  edits=%d  landed bytes=%d sha=%s' % (rel, len(edits), len(raw),
                                                            hashlib.sha256(raw).hexdigest()[:12]))
    cur = u
    for i, e in enumerate(edits):
        n = cur.count(e['anchor'])
        flag = 'OK ' if n == 1 else 'BAD'
        head = e['anchor'].split('\n')[0].strip()[:60]
        print('   [%s] edit %2d anchor_occurrences=%d  first=%s' % (flag, i + 1, n, head))
        if n != 1:
            return False
        cur = cur.replace(e['anchor'], e['repl'])
    d = cur.count('\n') - u.count('\n')
    out = cur.replace('\n', nl).encode('utf-8')
    if bom:
        out = b'\xef\xbb\xbf' + out
    crlf = out.count(b'\r\n')
    print('   net lines %+d  bytes %d -> %d  BOM=%s CRLF=%d bareLF=%d sha=%s'
          % (d, len(raw), len(out), out[:3] == b'\xef\xbb\xbf', crlf,
             out.count(b'\n') - crlf, hashlib.sha256(out).hexdigest()[:12]))
    after = markers(cur)
    moved = {k: (before[k], after[k]) for k in before if before[k] != after[k]}
    print('   markers moved: %s' % (moved if moved else 'none'))
    tmp = os.path.join(tempfile.gettempdir(), 'r65vfy_%s' % os.path.basename(path).replace('.json', '.py'))
    io.open(tmp, 'wb').write(out)
    try:
        py_compile.compile(tmp, doraise=True, cfile=tmp + 'c')
        ast.parse(out.decode('utf-8-sig'))
        print('   py_compile + ast.parse: OK')
    except Exception as e:
        print('   py_compile/ast FAILED: %s' % e)
        return False
    return all(v for v in [True])


if __name__ == '__main__':
    rc = [check(p) for p in sys.argv[1:]]
    print('ALL APPLY CLEAN =', all(rc))
