# -*- coding: utf-8 -*-
"""A1 corpus-wide blast-radius probe for the candidate "do not materialise the implicit terminal
return None" predicate.

The 402 landed products live in D:/Temp/r34gate/r34/build_head (verified byte-identical to a
fresh `landed`-arm run on the target file, and mirr_head/core is a copy of the current worktree
core).  This probe READS them and writes nothing outside A1: every variant .py and its explicit
`cfile` .pyc go to A1/corpus/.

For every function whose landed text ends with a trailing `return None` statement, drop exactly
that line and re-measure the strict reading of that function against the original code object.

usage: python -X utf8 corpus_drop.py <out-tag> [--nshard=N --shard=I] [--full]
"""
import difflib
import glob
import hashlib
import importlib.util
import io
import json
import os
import py_compile
import re
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r34gate/A1'
LAND = r'D:/Temp/r34gate/r34/build_head'
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')
_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

TMP = os.path.join(ROOT, 'corpus')
if not os.path.isdir(TMP):
    os.makedirs(TMP)

tag = sys.argv[1]
opts = dict(x[2:].split('=', 1) for x in sys.argv[2:] if '=' in x)
NS = int(opts.get('nshard', 1))
SH = int(opts.get('shard', 0))
LIMIT = 402 if opts.get('full') else 120

paths = [q.strip() for q in io.open(r'D:/Temp/r34gate/r34/all402.txt', encoding='utf-8') if q.strip()]


def slug(p):
    rel = p.replace('\\', '/')
    r0 = REPO.replace('\\', '/') + '/site-packages/'
    if rel.startswith(r0):
        rel = rel[len(r0):]
    return rel.replace('/', '__')[:-4].replace(':', '_')


def land_path(p):
    return os.path.join(LAND, slug(p) + 'OK.py')


paths = [p for i, p in enumerate(paths) if i % NS == SH and os.path.isfile(land_path(p))][:LIMIT]


def tok(i):
    if r10._is_jump(i.opname):
        return ('<JUMP>', r10._norm_jump_op(i.opname))
    return (r10._norm_arg(i), i.opname)


def cmp_pair(o, d):
    kind, msg, is_defect = r10.strict_compare(o, d)
    fo, fd = r10.filtered(o), r10.filtered(d)
    blocks = []
    if is_defect:
        for t, i1, i2, j1, j2 in difflib.SequenceMatcher(None, [tok(x) for x in fo],
                                                         [tok(x) for x in fd],
                                                         autojunk=False).get_opcodes():
            if t != 'equal':
                blocks.append([t, fo[i1].offset if i1 < len(fo) else -1,
                               [x.opname for x in fo[i1:i2]], [x.opname for x in fd[j1:j2]]])
    return {'defect': bool(is_defect), 'kind': kind, 'lo': len(fo), 'ld': len(fd),
            'delta': len(fd) - len(fo), 'blocks': blocks}


DEFRE = re.compile(r'^(\s*)(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(')


def defs_of(lines):
    """(name, start, lastline) for every def whose body is the following more-indented block."""
    out = []
    for k, l in enumerate(lines):
        m = DEFRE.match(l)
        if not m:
            continue
        ind = len(l) - len(l.lstrip())
        j = k + 1
        last = k
        while j < len(lines):
            cur = lines[j]
            if cur.strip():
                if (len(cur) - len(cur.lstrip())) <= ind:
                    break
                last = j
            j += 1
        out.append((m.group(2), k, last))
    return out


def compile_map(py):
    cfile = os.path.join(TMP, hashlib.sha1(py.encode('utf-8')).hexdigest()[:12] + '.pyc')
    py_compile.compile(py, cfile=cfile, doraise=True, quiet=2)
    return r10._load_map(cfile)


out = io.open(os.path.join(ROOT, 'corpus_drop.%s.jsonl' % tag), 'a', encoding='utf-8')
done = set()
for l in list(io.open(out.name, encoding='utf-8')):
    try:
        _r = json.loads(l)
        done.add(_r['func'] + '@' + _r['path'])
    except Exception:
        pass
nprobe = nimpr = nreg = nsame = ndef_before = ndef_after = 0
for p in paths:
    lp = land_path(p)
    try:
        origs = r10._load_map(p)
    except Exception as e:
        print('SKIP-LOAD %s %s' % (p, repr(e)[:80]))
        continue
    try:
        text = io.open(lp, encoding='utf-8-sig').read()
    except Exception:
        continue
    lines = text.replace('\r\n', '\n').split('\n')
    uid = hashlib.sha1(lp.encode('utf-8')).hexdigest()[:10]
    base_py = os.path.join(TMP, uid + '_land.py')
    io.open(base_py, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
    try:
        decs = compile_map(base_py)
    except Exception as e:
        print('SKIP-COMPILE %s %s' % (lp, repr(e)[:80]))
        continue
    key_by_tail = {}
    for kk in origs:
        key_by_tail.setdefault(kk.split('.')[-1], []).append(kk)
    for name, start, last in defs_of(lines):
        if lines[last].strip() != 'return None':
            continue
        keys = key_by_tail.get(name) or []
        if len(keys) != 1:
            continue
        key = keys[0]
        o = origs[key]
        if key + '@' + p in done:
            continue
        d = decs.get(keys[0])
        if d is None:
            continue
        before = cmp_pair(o, d)
        new = lines[:last] + lines[last + 1:]
        v_py = os.path.join(TMP, '%s_%s_drop.py' % (uid, name))
        io.open(v_py, 'w', encoding='utf-8', newline='\n').write('\n'.join(new))
        try:
            vmap = compile_map(v_py)
        except Exception:
            continue
        if name not in [q.split('.')[-1] for q in vmap]:
            continue
        after = cmp_pair(o, vmap[key])
        rec = {'path': p, 'func': key, 'landed': before, 'dropped': after}
        out.write(json.dumps(rec, ensure_ascii=False) + '\n')
        out.flush()
        nprobe += 1
        ndef_before += before['defect']
        ndef_after += after['defect']
        if before['defect'] and not after['defect']:
            nimpr += 1
            print('IMPROVED  %-58s %s  %d->%d delta%+d->%+d blk%d->%d'
                  % (key, os.path.basename(p), before['lo'], before['ld'], before['delta'],
                     after['delta'], len(before['blocks']), len(after['blocks'])))
        elif after['defect'] and not before['defect']:
            nreg += 1
            print('REGRESSED %-58s %s  %d->%d delta%+d->%+d blk%d->%d %s'
                  % (key, os.path.basename(p), before['lo'], before['ld'], before['delta'],
                     after['delta'], len(before['blocks']), len(after['blocks']),
                     json.dumps(after['blocks'][:1])[:220]))
        else:
            nsame += 1
            if before['defect'] != after['defect']:
                print('MOVED     %-58s %s' % (key, os.path.basename(p)))
out.close()
print('PROBED=%d defect_before=%d defect_after=%d IMPROVED=%d REGRESSED=%d UNCHANGED=%d (files=%d)'
      % (nprobe, ndef_before, ndef_after, nimpr, nreg, nsame, len(paths)))
