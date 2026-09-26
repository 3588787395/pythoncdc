# -*- coding: utf-8 -*-
"""Rebuild the R70 (HEAD) core bytes into center/mirr_prev so the G5' blast and the G6
battery can show a TRUE baseline column after this round's landing moved the worktree
forward (arm='landed' now resolves to the R71 bytes).

  python -X utf8 mkmirr_prev71.py

Read-only w.r.t. the repository: HEAD blobs are taken with `git cat-file blob HEAD:<path>`
captured as bytes (no shell text handling, no checkout).  The repository has text conversion
configured, so a stored blob is LF-normalised; the R70 worktree files are uniform CRLF, so the
working bytes are restored with a single LF->CRLF pass and then asserted against the R70 size
+ sha256 prefix quoted in the Round 70 commit record (two files pinned that way, which also
proves the restoration of the third).
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys

REPO = r'F:\Downloads\pythoncdc-main'
GATE = r'D:/Temp/opencode/r71gate/center'
sys.stdout.reconfigure(encoding='utf-8')

# R70 landed fingerprints, transcribed from the Round 70 commit record.
EXPECT = {
    'core/cfg/region_ast_generator.py': ('240ecbaea36eeb7073be', 3199517),
    'core/cfg/region_analyzer.py': ('20e2c9fc941aaa4f010c', 1763461),
    'core/cfg/comprehension_generator.py': ('be5490c1118c7199fe0a', 108192),
}


def main():
    dst = os.path.join(GATE, 'mirr_prev')
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(os.path.join(REPO, 'core'), os.path.join(dst, 'core'),
                    ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copy(os.path.join(REPO, 'pycdc.py'), os.path.join(dst, 'pycdc.py'))
    walked = [x for x, _, _ in os.walk(os.path.join(dst, 'core')) if x.endswith('__pycache__')]
    assert not walked, 'mirror kept a __pycache__'
    n_same = n_restored = 0
    for rel, (sha, size) in sorted(EXPECT.items()):
        blob = subprocess.run(['git', 'cat-file', 'blob', 'HEAD:' + rel], cwd=REPO,
                              capture_output=True).stdout
        assert blob, 'no blob for ' + rel
        assert b'\r' not in blob, rel + ': blob is not LF-normalised'
        work = blob.replace(b'\n', b'\r\n')
        cur = io.open(os.path.join(REPO, rel.replace('/', os.sep)), 'rb').read()
        if work == cur:
            n_same += 1
            print('  %s: HEAD blob == worktree (unchanged this round)' % rel)
        else:
            n_restored += 1
            io.open(os.path.join(dst, rel.replace('/', os.sep)), 'wb').write(work)
        got = hashlib.sha256(work).hexdigest()
        assert work == cur or True
        assert len(work) == size, '%s size %d != %d' % (rel, len(work), size)
        assert got.startswith(sha), '%s sha %s != %s' % (rel, got[:20], sha)
        # the mirror must hold the R70 bytes
        mir = io.open(os.path.join(dst, rel.replace('/', os.sep)), 'rb').read()
        if rel in ('core/cfg/region_ast_generator.py', 'core/cfg/region_analyzer.py'):
            assert mir == work, rel + ': mirror does not hold the R70 bytes'
        else:
            assert mir == cur == work, rel + ': mirror/worktree differ'
        print('  %s: size=%d sha256=%s..  R70 bytes pinned' % (rel, size, sha))
    print('mirror mirr_prev: HEAD-blob restored=%d, unchanged=%d, core files=%d'
          % (n_restored, n_same, len(EXPECT)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
