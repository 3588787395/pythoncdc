# -*- coding: utf-8 -*-
"""Build one candidate mirror from ANY number of specs (one spec per core file).

  python -X utf8 mbuild.py <dst-name> <spec.json> [<spec.json> ...]

Each spec is the agent format {"file": "core/cfg/<x>.py", "anchor"/"repl" or "edits":[...]}.
Assertions, in order, per spec:
  * the pristine mirror copy of that file is byte-identical to the worktree file,
  * every anchor occurs exactly once in the current (already-patched) mirror text,
  * the UTF-8 BOM state is preserved,
  * line endings stay uniform (all CRLF or all LF),
  * the net inserted line count equals what the spec claims.
Nothing is written outside D:/Temp/opencode/r65gate.
"""
import io
import json
import os
import shutil
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/opencode/r65gate'
CR = chr(13)
ALLOWED = ('core/cfg/region_ast_generator.py', 'core/cfg/region_analyzer.py')
sys.stdout.reconfigure(encoding='utf-8')


def _mkmirror(dst):
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    shutil.copytree(os.path.join(REPO, 'core'), os.path.join(dst, 'core'),
                    ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copy(os.path.join(REPO, 'pycdc.py'), os.path.join(dst, 'pycdc.py'))
    assert not [x for x, _, _ in os.walk(dst) if x.endswith('__pycache__')], 'mirror kept __pycache__'
    return dst


def main():
    dst = ROOT + '/mirr_' + sys.argv[1]
    specs = sys.argv[2:]
    assert specs, 'usage: mbuild.py <dst> <spec.json> ...'
    _mkmirror(dst)
    seen = {}
    for sp in specs:
        spec = json.load(io.open(sp, encoding='utf-8'))
        rel = spec['file']
        assert rel in ALLOWED, rel
        assert rel not in seen, 'two specs for %s -- merge them first' % rel
        seen[rel] = sp
        mp = os.path.join(dst, rel.replace('/', os.sep))
        wp = os.path.join(REPO, rel.replace('/', os.sep))
        assert io.open(mp, 'rb').read() == io.open(wp, 'rb').read(), 'mirror != worktree for %s' % rel
        raw = io.open(wp, 'rb').read()
        bom = raw[:3] == b'\xef\xbb\xbf'
        src = raw.decode('utf-8-sig')
        nl = '\r\n' if src.count(CR) else '\n'
        u = src.replace('\r\n', '\n')
        assert CR not in u, 'mixed line endings in %s' % rel
        edits = spec.get('edits') or [{'anchor': spec['anchor'], 'repl': spec['repl']}]
        patched = u
        for k, e in enumerate(edits):
            n = patched.count(e['anchor'])
            assert n == 1, '%s edit %d anchor occurrences=%d' % (os.path.basename(sp), k, n)
            patched = patched.replace(e['anchor'], e['repl'])
        assert patched != u, '%s made no change' % sp
        ins = sum(e['repl'].count('\n') - e['anchor'].count('\n') for e in edits)
        out = patched.replace('\n', nl).encode('utf-8')
        if bom:
            out = b'\xef\xbb\xbf' + out
        _crlf = out.count(b'\r\n')
        # base-style aware: a pure-LF base (region_ast_generator.py after the R64
        # reflow) has no CR at all, so the old "every \n is part of a \r\n" test
        # could never hold.  What must be preserved is *uniformity* with the base.
        if nl == '\r\n':
            assert out.count(b'\n') == _crlf, 'mixed line endings after patch'
        else:
            assert out.count(b'\r') == 0, 'mixed line endings after patch'
        assert out.count(b'\n') - u.count('\n') == ins, 'inserted line count mismatch'
        io.open(mp, 'wb').write(out)
        print('  patched %-34s edits=%d lines=%+d bytes %d -> %d BOM=%s'
              % (rel, len(edits), ins, len(raw), len(out), bom))
    print('mirror ready: %s  from %d spec(s) %s' % (dst, len(specs), [os.path.basename(s) for s in specs]))


main()
