"""Land R45-A byte-exactly: copy the gated arm bytes over the worktree generator."""
import hashlib
import io
import shutil

REPO = r'F:\Downloads\pythoncdc-main'
ARM = r'D:/Temp/r43gate/mirr_r45a'
rel = 'core/cfg/region_ast_generator.py'
wt = REPO + '/' + rel
src = ARM + '/' + rel


def sha(p, n=20):
    return hashlib.sha256(io.open(p, 'rb').read()).hexdigest()[:n]


def stats(p):
    b = io.open(p, 'rb').read()
    return (len(b), b.count(b'\r\n'), b.count(b'\n'), b[:3] == b'\xef\xbb\xbf', b.count(b'\n') - b.count(b'\r\n'))


print('pre-land worktree sha20=%s %s' % (sha(wt), stats(wt)))
print('arm        sha20=%s %s' % (sha(src), stats(src)))
assert sha(wt, 20) == 'd4c430303a5d2b63753d', 'worktree generator != expected landed bytes'
shutil.copyfile(src, wt)
print('post-land  sha20=%s %s' % (sha(wt), stats(wt)))
assert sha(wt) == sha(src), 'landing is not byte-exact'
n, cr, lf, bom, extra = stats(wt)
assert bom, 'lost UTF-8 BOM'
assert extra == 0, 'mixed line endings (%d bare LF)' % extra
pn, pcr, plf, pb, pe = stats(REPO + '/core/cfg/region_analyzer.py')
print('analyzer untouched sha20=%s %s' % (sha(REPO + '/core/cfg/region_analyzer.py'), (pn, pcr, plf, pb, pe)))
assert sha(REPO + '/core/cfg/region_analyzer.py', 20) == '55a9f61b9b0703063d44', 'analyzer drifted'
