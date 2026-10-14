"""Full-corpus regen + CR-stripped compare against `git archive HEAD`.

Regenerates every pyc in pyc_index.json into MIRROR products, extracts the committed
products with git archive (no checkout CRLF conversion), strips CR from both sides and
lists the CHANGED files.
"""
import json
import os
import subprocess
import sys

MIRROR = 'D:/Temp/r91'
REPO = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main'
IDX = REPO + '/pyc_index.json'
HEAD = 'D:/Temp/r91/head_products'
NEW = 'D:/Temp/r91/new_products'

env = dict(os.environ, PYTHONIOENCODING='utf-8')
entries = json.load(open(IDX, encoding='utf-8'))
paths = [e['path'] if isinstance(e, dict) else e for e in entries]
paths = [p for p in paths if p.endswith('.pyc')]


def rel_of(p):
    p = p.replace(chr(92), '/')
    k = p.lower().find('site-packages/')
    return p[k:] if k >= 0 else os.path.basename(p)


paths = [rel_of(p) for p in paths]
print('corpus=%d' % len(paths), flush=True)

os.makedirs(NEW, exist_ok=True)
os.makedirs(HEAD, exist_ok=True)

# 1. committed products via git archive
if not os.path.exists(HEAD + '/.done'):
    tar = 'D:/Temp/r91/_head.tar'
    subprocess.run(['git', '-C', REPO, 'archive', '--format=tar', '-o', tar, 'HEAD'], check=True)
    subprocess.run(['tar', '-xf', tar, '-C', HEAD], check=True)
    open(HEAD + '/.done', 'wb').close()

fail = 0
for i, rel in enumerate(paths):
    pyc = REPO + '/' + rel
    if not os.path.exists(pyc):
        print('MISSING %s' % pyc, flush=True)
        fail += 1
        continue
    tag = '%03d' % i
    out = NEW + '/' + tag + '.py'
    if os.path.exists(out):
        os.remove(out)
    try:
        subprocess.run([sys.executable, '-X', 'utf8', 'pycdc.py', pyc, '-o', out],
                       cwd=MIRROR, capture_output=True, timeout=300)
    except subprocess.TimeoutExpired:
        pass
    if not os.path.exists(out) or os.path.getsize(out) < 100:
        print('PRODUCER-FAIL %s' % rel, flush=True)
        fail += 1
print('regen done fail=%d' % fail, flush=True)

changed = []
for i, rel in enumerate(paths):
    tag = '%03d' % i
    np = NEW + '/' + tag + '.py'
    hp = os.path.join(HEAD, rel.replace('\\', '/'))
    if not os.path.exists(hp):
        alt = HEAD + '/site-packages/' + os.path.relpath(rel, 'site-packages').replace('\\', '/') \
            if 'site-packages' in rel else None
        hp = alt if alt and os.path.exists(alt) else hp
    if not os.path.exists(hp):
        print('NO-HEAD %s' % rel, flush=True)
        continue
    if not os.path.exists(np):
        changed.append((rel, 'missing-new'))
        continue
    a = open(np, 'rb').read().replace(b'\r', b'')
    b = open(hp, 'rb').read().replace(b'\r', b'')
    if a != b:
        changed.append((rel, '%d->%d' % (len(b), len(a))))
print('CHANGED=%d' % len(changed), flush=True)
for rel, info in changed:
    print('  %s %s' % (rel, info), flush=True)
