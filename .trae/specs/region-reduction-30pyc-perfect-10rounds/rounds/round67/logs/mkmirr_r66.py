# -*- coding: utf-8 -*-
"""Rebuild the R66 (HEAD) core bytes into center/mirr_r66 so the G6 battery can show a TRUE
baseline column after this round's landing moved the worktree forward.

  python -X utf8 mkmirr_r66.py

Read-only w.r.t. the repository: the HEAD blobs are taken with `git cat-file blob HEAD:<path>`
captured as bytes (no shell text handling, no checkout).  NOTE the repository has text
conversion configured, so a stored blob is LF-normalised; each R66 file is recorded as uniform
CRLF with 0 bare LF, so the working bytes are restored with a single LF->CRLF pass and then
asserted against the R66 size + sha256 prefix quoted in the Round 66 commit record.  Two files
are pinned that way, which also proves the restoration is right for the third.
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys

REPO = r'F:/Downloads/pythoncdc-main'
GATE = r'D:/Temp/opencode/r67gate/center'
sys.stdout.reconfigure(encoding='utf-8')

# R66 landed fingerprints, transcribed from the Round 66 commit record.
EXPECT = {
    'core/cfg/region_ast_generator.py': ('3db80082b87ecca06e8c', 3140634),
    'core/cfg/region_analyzer.py': ('0e9740cc1836f3201312', 1734099),
}


def restore(blob):
    """Stored blob is LF-normalised; put the CR back exactly where the working file had it."""
    assert b'\r' not in blob, 'blob already carries CR, restoration would double it'
    return blob.replace(b'\n', b'\r\n')


dst = os.path.join(GATE, 'mirr_r66')
if os.path.isdir(dst):
    shutil.rmtree(dst)
os.makedirs(dst)
shutil.copytree(os.path.join(REPO, 'core'), os.path.join(dst, 'core'),
                ignore=shutil.ignore_patterns('__pycache__'))
shutil.copy(os.path.join(REPO, 'pycdc.py'), os.path.join(dst, 'pycdc.py'))
assert not [x for x, _, _ in os.walk(dst) if x.endswith('__pycache__')], 'mirror kept __pycache__'

for rel in sorted(EXPECT) + ['core/cfg/comprehension_generator.py']:
    r = subprocess.run(['git', '-C', REPO, 'cat-file', 'blob', 'HEAD:' + rel],
                       capture_output=True)
    assert r.returncode == 0, 'git cat-file failed for %s: %s' % (rel, r.stderr[:200])
    blob = restore(r.stdout)
    p = os.path.join(dst, rel.replace('/', os.sep))
    wt = io.open(p, 'rb').read()
    io.open(p, 'wb').write(blob)
    sha = hashlib.sha256(blob).hexdigest()
    print('%-40s HEAD %d B sha256=%s | worktree %d B sha256=%s | same=%s'
          % (rel, len(blob), sha[:20], len(wt), hashlib.sha256(wt).hexdigest()[:20], blob == wt))
    if rel in EXPECT:
        pref, size = EXPECT[rel]
        assert sha.startswith(pref) and len(blob) == size, \
            'R66 fingerprint mismatch for %s: got sha %s size %d, expected %s / %d' % (
                rel, sha[:20], len(blob), pref, size)
        assert blob != wt, '%s: HEAD blob equals worktree, so nothing was restored' % rel
    assert blob.count(b'\r\n') > 0 and blob.count(b'\n') == blob.count(b'\r\n'), \
        '%s: restored bytes are not uniform CRLF' % rel
print('mirr_r66 ready (asserts passed)')
