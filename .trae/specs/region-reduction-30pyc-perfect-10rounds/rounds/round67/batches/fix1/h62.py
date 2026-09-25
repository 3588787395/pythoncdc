# -*- coding: utf-8 -*-
"""Round 27 mirror harness: build two private cores, measure per-file, tally an A/B.

Generic over r26a.py: the candidate patch is not baked in, it is read from a spec json so
whichever diagnosed candidate wins can be measured without editing this file:

  {"file": "core/cfg/region_ast_generator.py",
   "anchor": "<exact LF-normalised text, must occur exactly once>",
   "repl":   "<replacement text>"}

usage:
  python -X utf8 r27.py build --spec=<spec.json>
  python -X utf8 r27.py run --arm=head|cand|landed --list=<txt> --out=<jsonl> [--nshard=N --shard=I] [--budget=SEC]
  python -X utf8 r27.py ab --a=<head.jsonl> --b=<cand.jsonl>
"""
import hashlib
import io
import json
import os
import shutil
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/opencode/r67gate/fix1'
CR = chr(13)
BS = chr(92)
sys.stdout.reconfigure(encoding='utf-8')


def _target(rel):
    return os.path.join(REPO, rel.replace('/', os.sep))


def _mkmirror(dst, rel):
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    shutil.copytree(os.path.join(REPO, 'core'), os.path.join(dst, 'core'), ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copy(os.path.join(REPO, 'pycdc.py'), os.path.join(dst, 'pycdc.py'))
    walked=[x for x,_,_ in os.walk(os.path.join(dst,'core')) if x.endswith('__pycache__')]
    assert not walked, 'mirror kept a __pycache__'
    return os.path.join(dst, rel)


def build(spec_path, dst='cand'):
    spec = json.load(io.open(spec_path, encoding='utf-8'))
    rel = spec['file']
    edits = spec.get('edits') or [{'anchor': spec['anchor'], 'repl': spec['repl']}]
    assert rel in ('core/cfg/region_ast_generator.py', 'core/cfg/region_analyzer.py'), rel
    head = _mkmirror(ROOT + '/mirr_head', rel)
    cand = _mkmirror(ROOT + '/mirr_' + dst, rel)
    src = io.open(head, encoding='utf-8-sig', newline='').read()
    nl = '\r\n' if src.count(CR) else '\n'
    u = src.replace(nl, '\n')
    patched = u
    for k, e in enumerate(edits):
        n = patched.count(e['anchor'])
        assert n == 1, 'edit %d anchor occurrences=%d' % (k, n)
        patched = patched.replace(e['anchor'], e['repl'])
    assert patched != u and patched.count(u[:200]) == 1, 'patch did not apply'
    head_bom = io.open(head, 'rb').read(3) == b'\xef\xbb\xbf'
    io.open(cand, 'w', encoding='utf-8' + ('-sig' if head_bom else ''), newline='').write(
        patched.replace('\n', nl))
    if head_bom:
        assert io.open(cand, 'rb').read(3) == b'\xef\xbb\xbf', 'candidate lost the BOM'
    assert io.open(head, 'rb').read() == io.open(_target(rel), 'rb').read(), 'head mirror != worktree core'
    _cb = io.open(cand, 'rb').read()
    _crlf = _cb.count(b'\r\n')
    assert _cb.count(b'\n') == _crlf, 'candidate line endings were mixed'
    assert (_crlf - src.count(CR)) == sum(e['repl'].count('\n') - e['anchor'].count('\n')
                                          for e in edits), 'unexpected inserted line count'
    print('mirrors built: head pristine == worktree bytes, cand patched (%d edits, %s, BOM=%s, nl=%s)'
          % (len(edits), rel, head_bom, 'CRLF' if nl == '\r\n' else 'LF'))


def _load_arm(arm):
    core = (REPO if arm == 'landed' else
            ROOT + ('/mirr_head' if arm == 'head' else '/mirr_' + arm)).replace(BS, '/')
    if arm == 'landed':
        sys.path.insert(0, REPO)
    for m in [k for k, mod in list(sys.modules.items())
              if getattr(mod, '__file__', None)
              and os.path.abspath(mod.__file__).replace('\\', '/').startswith(ROOT)]:
        del sys.modules[m]
    sys.path.insert(0, core)
    sys.path.append(REPO)
    import pycdc
    got = os.path.dirname(os.path.abspath(pycdc.__file__)).replace('\\', '/')
    assert got == core, 'pycdc resolved to %s not %s' % (got, core)
    return pycdc


def run(arm, listfile, out, opts=None):
    opts = opts or {}
    pycdc = _load_arm(arm)
    import importlib.util as iu
    _s = iu.spec_from_file_location('pbv', os.path.join(REPO, 'scripts', 'pyc_batch_verify.py'))
    pbv = iu.module_from_spec(_s)
    _s.loader.exec_module(pbv)
    if not os.path.isdir(ROOT + '/build_' + arm):
        os.makedirs(ROOT + '/build_' + arm)
    done = set()
    if os.path.isfile(out):
        for l in io.open(out, encoding='utf-8'):
            try:
                _r = json.loads(l)
                done.add(_r.get('arm') + '|' + _r['path'])
            except Exception:
                pass
    paths = [l.strip() for l in io.open(listfile, encoding='utf-8') if l.strip()]
    nshard = int(opts.get('nshard', 1))
    shard = int(opts.get('shard', 0))
    paths = [q for i, q in enumerate(paths) if i % nshard == shard]
    budget = float(opts.get('budget', 1e9))
    import time as _t
    t0 = _t.time()
    paths = [q for q in paths if arm + '|' + q not in done and (_t.time() - t0 <= budget or not paths)]
    fh = io.open(out, 'a', encoding='utf-8')
    for p in paths:
        rel = p.replace('\\', '/')
        r0 = REPO.replace('\\', '/') + '/site-packages/'
        if rel.startswith(r0):
            rel = rel[len(r0):]
        dst = os.path.join(ROOT + '/build_' + arm,
                           rel.replace('/', '__')[:-4].replace(':', '_') + 'OK.py').replace('\\', '/')
        rec = {'path': p, 'arm': arm}
        try:
            text = pycdc.decompile_pyc(p)
            io.open(dst, 'w', encoding='utf-8').write(text)
            rec['sha'] = hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
            r = pbv.bytecode_diff(p, dst)
            rec['total_functions'] = r.get('total_functions')
            rec['matched_functions'] = r.get('matched_functions')
            rec['mism'] = [[m.get('name'), m.get('orig_count'), m.get('decomp_count'),
                            m.get('jump_diffs'), m.get('true_diffs')]
                           for m in (r.get('mismatches') or [])]
            assert rec['total_functions'], 'empty reading for %s' % p
        except Exception as e:
            rec['error'] = repr(e)[:200]
        fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
        fh.flush()
        print('%s %-28s %s/%s  %s  %s' % (arm, os.path.basename(p), rec.get('matched_functions'),
                                          rec.get('total_functions'), rec.get('mism'), rec.get('error', '')))
    fh.close()


def ab(a_path, b_path):
    def load(f):
        d = {}
        for l in io.open(f, encoding='utf-8'):
            if l.strip():
                r = json.loads(l)
                d[r['path']] = r
        return d
    A, B = load(a_path), load(b_path)
    only = set(A) ^ set(B)
    same = imp = reg = mov = err = 0
    lines = []
    for p in sorted(set(A) & set(B)):
        a, b = A[p], B[p]
        if a.get('error') or b.get('error'):
            err += 1
            lines.append('ERR    %s %s / %s' % (p, a.get('error'), b.get('error')))
            continue
        if a.get('sha') == b.get('sha'):
            same += 1
            continue
        ga = a.get('matched_functions', 0)
        gb = b.get('matched_functions', 0)
        if gb > ga:
            imp += 1
            lines.append('IMPROVED %s  %s/%s -> %s/%s' % (p, ga, a['total_functions'], gb, b['total_functions']))
        elif gb < ga:
            reg += 1
            lines.append('REGRESSION %s  %s/%s -> %s/%s' % (p, ga, a['total_functions'], gb, b['total_functions']))
        else:
            mov += 1
            sa, sb = set(map(str, a.get('mism') or [])), set(map(str, b.get('mism') or []))
            lines.append('MOVED  %s  gained=%s lost=%s' % (p, sorted(sb - sa), sorted(sa - sb)))
            for x, y in zip(sorted(a.get('mism') or []), sorted(b.get('mism') or [])):
                if x != y:
                    lines.append('    ~ %s %s -> %s' % (x[0], x[1:], y[1:]))
    for l in lines:
        print(l)
    print('TALLY SAME=%d IMPROVED=%d REGRESSION=%d MOVED=%d ERR=%d  (unpaired lists=%d)'
          % (same, imp, reg, mov, err, len(only)))
    print('files fully matched: a=%d b=%d'
          % (sum(1 for p in A if A[p].get('matched_functions') == A[p].get('total_functions')
                 and A[p].get('total_functions') and not A[p].get('error')),
             sum(1 for p in B if B[p].get('matched_functions') == B[p].get('total_functions')
                 and B[p].get('total_functions') and not B[p].get('error'))))


if __name__ == '__main__':
    cmd = sys.argv[1]
    kw = dict(x[2:].split('=', 1) for x in sys.argv[2:])
    if cmd == 'build':
        build(kw['spec'], kw.get('dst', 'cand'))
    elif cmd == 'run':
        run(kw['arm'], kw['list'], kw['out'], kw)
    elif cmd == 'ab':
        ab(kw['a'], kw['b'])
    else:
        raise SystemExit('unknown command %s' % cmd)
