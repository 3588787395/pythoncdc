# -*- coding: utf-8 -*-
"""Round 63 landing step: replay the *measured* mirror spec onto the real core file and
prove byte-equality with that mirror.

  python -X utf8 land29.py --spec=<spec.json> [--mirror=mirr_cand] [--apply]

The spec is the same json the mirror harness consumed ({"file", "edits":[{anchor, repl}]}
with LF-normalised text), so what lands is literally what was measured -- no hand-typing.
"""
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/opencode/r67gate'
BS = os.sep
CR = chr(13)


def _args():
    kw = dict(x[2:].split('=', 1) for x in sys.argv[2:] if x.startswith('--') and '=' in x)
    return kw


def main():
    cmd = sys.argv[1]
    assert cmd == 'land', 'usage: land29.py land --spec=<json> [--mirror=mirr_cand] [--apply]'
    a = _args()
    spec = json.load(io.open(a['spec'], encoding='utf-8'))
    rel = spec['file']
    edits = spec.get('edits') or [{'anchor': spec['anchor'], 'repl': spec['repl']}]
    assert rel in ('core/cfg/region_ast_generator.py', 'core/cfg/region_analyzer.py',
                     'core/cfg/comprehension_generator.py'), rel
    dst = os.path.join(REPO, rel.replace('/', BS))
    mirror = os.path.join(ROOT, a.get('mirror', 'mirr_cand'), rel.replace('/', BS))

    raw = io.open(dst, 'rb').read()
    head_bom = raw[:3] == b'\xef\xbb\xbf'
    src = raw.decode('utf-8-sig')
    nl = '\r\n' if src.count(CR) else '\n'
    u = src.replace('\r\n', '\n')
    assert CR not in u, 'worktree file has mixed line endings'
    patched = u
    for k, e in enumerate(edits):
        n = patched.count(e['anchor'])
        assert n == 1, 'edit %d anchor occurrences=%d -- not what was measured' % (k, n)
        patched = patched.replace(e['anchor'], e['repl'])
    assert patched != u, 'spec made no change'
    ins = sum(e['repl'].count('\n') - e['anchor'].count('\n') for e in edits)
    out = patched.replace('\n', nl).encode('utf-8')
    if head_bom:
        out = b'\xef\xbb\xbf' + out
    mir = io.open(mirror, 'rb').read()
    print('spec %s  file %s  edits %d  inserted lines %d  nl=%s  BOM=%s'
          % (os.path.basename(a['spec']), rel, len(edits), ins,
             'CRLF' if nl == '\r\n' else 'LF', head_bom))
    assert out == mir, 'replay does not reproduce the measured mirror %s' % mirror
    print('replay == measured mirror bytes: OK (%s, %d bytes)' % (os.path.basename(mirror), len(mir)))
    if '--apply' not in sys.argv:
        print('dry run; pass --apply to write %s' % dst)
        return
    io.open(dst, 'wb').write(out)
    after = io.open(dst, 'rb').read()
    assert after == out == mir, 'landing did not land byte-exactly'
    assert (after[:3] == b'\xef\xbb\xbf') == head_bom, 'BOM state changed'
    _crlf = after.count(b'\r\n')
    assert after.count(b'\n') == _crlf, 'mixed line endings after landing'
    print('applied: %d -> %d bytes, CRLF %d, BOM=%s, equals measured mirror=%s'
          % (len(raw), len(after), _crlf, head_bom, mir == after))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
