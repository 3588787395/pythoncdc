import hashlib
import os
import shutil
import subprocess
import sys

M = 'D:/Temp/r91m'
GEN = M + '/core/cfg/region_ast_generator.py'
PG = M + '/gen_base_566ff5c502276e48.py'
ANA = M + '/core/cfg/region_analyzer.py'
PA = M + '/ana_base_996a1b1acf143458.py'
ROOT = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main'
SPR = os.path.join(ROOT, '.trae/specs', 'region-reduction-v3-full-corpus-100pct-10rounds')
R79 = os.path.join(SPR, 'rounds/round41/CANDIDATE_r2179_3ad5ceaa23135334.py')
CL = os.path.join(SPR, 'rounds/round40/r95/corpus402.txt')
LAND = os.path.join(ROOT, 'core/cfg/region_ast_generator.py')


def h16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


paths = [os.path.join(ROOT, l.strip()) for l in open(CL, encoding='utf-8') if l.strip()]
want = {'realtime_event_source.pyc': 'realtime', 'quote.pyc': 'quote',
        'real_quote.pyc': 'real_quote', 'trade_live_broker.pyc': 'broker',
        'function.pyc': 'function', 'replace_utils.pyc': 'replace_utils',
        'quotation.pyc': 'quotation', 'order_api.pyc': 'order_api',
        'klinedata.pyc': 'klinedata', 'handlers.pyc': 'handlers'}
PYCS = {}
for p in paths:
    b = os.path.basename(p)
    if b in want:
        PYCS.setdefault(want[b], p)

src = open(LAND, 'rb').read().decode('utf-8-sig')
lines = src.split('\r\n')
print('--- context around 26880..26925 (landed bytes) ---')
for i in range(26879, 26925):
    print('  %d: %s' % (i + 1, lines[i][:118]))


def build(neut_lines, tag):
    out = list(lines)
    for ln in neut_lines:
        i = ln - 1
        s = out[i]
        assert 'self.generated_blocks.add' in s, 'line %d is not a claim: %r' % (ln, s[:80])
        out[i] = ' ' * (len(s) - len(s.lstrip())) + 'pass'
    body = ('\ufeff' + '\r\n'.join(out)).lstrip('\ufeff').encode('utf-8')
    p = 'D:/Temp/merge_r108/gen_%s.py' % tag
    open(p, 'wb').write(body)
    b = open(p, 'rb').read()
    compile(b.decode('utf-8-sig'), p, 'exec')
    print('%s sha16=%s size=%d bareLF=%d CRCRCR=%d compile OK' % (
        tag, h16(p), len(b), sum(1 for i, c in enumerate(b) if c == 10 and (i == 0 or b[i - 1] != 13)),
        b.count(b'\r\r\n')), flush=True)
    return p


def committed(pyc):
    ok = pyc[:-4] + 'OK.py'
    return open(ok, 'rb').read().replace(b'\r\n', b'\n') if os.path.exists(ok) else None


def measure(variant, label):
    print('=== measure %s (%s) ===' % (label, h16(variant)), flush=True)
    try:
        shutil.copyfile(R79, ANA)
        shutil.copyfile(variant, GEN)
        for k, p in sorted(PYCS.items()):
            r = subprocess.run([sys.executable, '-X', 'utf8', M + '/pycdc.py', p],
                               capture_output=True, cwd=M, timeout=120)
            q = r.stdout.replace(b'\r\n', b'\n')
            c = committed(p)
            st = 'IDENTICAL' if c is not None and q == c else 'CHANGED'
            if len(r.stdout) < 2000:
                st = 'STUB/' + st
            print('   %-12s rc=%d bytes=%d %s' % (k, r.returncode, len(r.stdout), st), flush=True)
            if k == 'realtime' and len(r.stdout) > 2000:
                o = M + '/out/rt_%s.py' % label
                open(o, 'wb').write(r.stdout)
                j = subprocess.run([sys.executable, '-X', 'utf8', SPR + '/rounds/round41/oracle_diff_r104.py', o],
                                   capture_output=True, timeout=140)
                for l in j.stdout.decode('utf-8', 'replace').splitlines():
                    if 'ours=' in l or 'DELTAS' in l or 'indeg' in l or 'units=' in l:
                        print('     ', l.strip(), flush=True)
    finally:
        shutil.copyfile(PG, GEN)
        shutil.copyfile(PA, ANA)
        print('   restored ana=%s gen=%s' % (h16(ANA) == '996a1b1acf143458', h16(GEN) == '566ff5c502276e48'), flush=True)


NEEDED = [22505, 26911]
FIVE = [22501, 22530, 22534, 22539]
assert 'self.generated_blocks.add' in lines[26910], lines[26910][:90]
v1 = build(NEEDED, 'r2185_neuter26911')
measure(v1, 'neuter26911')
if '--all6' in sys.argv:
    v2 = build(sorted(set(NEEDED + FIVE)), 'r2185_neuter_all6')
    measure(v2, 'neuter_all6')
