"""Land R49-A byte-exactly: copy the gated arm bytes over the worktree analyzer."""
import hashlib
import io
import shutil

REPO = r'F:\Downloads\pythoncdc-main'
ARM = r'D:/Temp/r43gate/mirr_r49a'
rel = 'core/cfg/region_analyzer.py'
wt = REPO + '/' + rel
src = ARM + '/' + rel
PRE = '0e1c4ce1417f'
GEN_PRE = '2a3d522b0ec9'


def sha(p, n=20):
    return hashlib.sha256(io.open(p, 'rb').read()).hexdigest()[:n]


def stats(p):
    b = io.open(p, 'rb').read()
    return (len(b), b.count(b'\r\n'), b.count(b'\n'), b[:3] == b'\xef\xbb\xbf',
            b.count(b'\n') - b.count(b'\r\n'))


print('pre-land worktree sha20=%s %s' % (sha(wt), stats(wt)))
print('arm        sha20=%s %s' % (sha(src), stats(src)))
assert sha(wt, 12) == PRE, 'worktree analyzer != expected landed bytes'
shutil.copyfile(src, wt)
print('post-land  sha20=%s %s' % (sha(wt), stats(wt)))
assert sha(wt) == sha(src), 'landing is not byte-exact'
n, cr, lf, bom, extra = stats(wt)
assert not bom, 'analyzer must stay BOM-free'
assert extra == 0, 'mixed line endings (%d bare LF)' % extra
gn, gcr, glf, gb, ge = stats(REPO + '/core/cfg/region_ast_generator.py')
print('generator untouched sha20=%s %s' % (sha(REPO + '/core/cfg/region_ast_generator.py'),
                                           (gn, gcr, glf, gb, ge)))
assert sha(REPO + '/core/cfg/region_ast_generator.py', 12) == GEN_PRE, 'generator drifted'
