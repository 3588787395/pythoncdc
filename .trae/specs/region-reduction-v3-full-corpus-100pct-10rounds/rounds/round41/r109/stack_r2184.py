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
R81 = os.path.join(SPR, 'rounds/round41/r108/CANDIDATE_r2181_8da14b53a94e07c3.py')
CL = os.path.join(SPR, 'rounds/round40/r95/corpus402.txt')


def h16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


paths = [os.path.join(ROOT, l.strip()) for l in open(CL, encoding='utf-8') if l.strip()]
want = {'realtime_event_source.pyc': 'realtime', 'quote.pyc': 'quote',
        'real_quote.pyc': 'real_quote', 'trade_live_broker.pyc': 'broker',
        'function.pyc': 'function', 'replace_utils.pyc': 'replace_utils',
        'order_api.pyc': 'order_api', 'quotation.pyc': 'quotation'}
PYCS = {}
for p in paths:
    b = os.path.basename(p)
    if b in want:
        PYCS.setdefault(want[b], p)

src = open(R81, 'rb').read().decode('utf-8-sig')
lines = src.split('\r\n')
NEEDLE = 'self.generated_blocks.add(b)'
idx = [i for i, l in enumerate(lines) if l.strip() == NEEDLE]
print('R21-81 candidate: bare claim statements found at lines', [i + 1 for i in idx], flush=True)
# restrict to the _if_generate_normal neighbourhood: find the def line and use the following 1600 lines
start = next(i for i, l in enumerate(lines) if l.strip().startswith('def _if_generate_normal('))
stop = start + 1700
inside = [i for i in idx if start <= i < stop]
print('_if_generate_normal def at %d; claims inside: %s' % (start + 1, [i + 1 for i in inside]), flush=True)
for i in inside:
    lines[i] = ' ' * (len(lines[i]) - len(lines[i].lstrip())) + 'pass'
new = ('\ufeff' + '\r\n'.join(lines)).lstrip('\ufeff').encode('utf-8')
out = 'D:/Temp/merge_r108/gen_r2184_ledger_plus_neuter.py'
open(out, 'wb').write(new)
b2 = open(out, 'rb').read()
print('stack sha16=%s size=%d bareLF=%d CRCRCR=%d' % (
    h16(out), len(b2), sum(1 for i, c in enumerate(b2) if c == 10 and (i == 0 or b2[i - 1] != 13)),
    b2.count(b'\r\r\n')), flush=True)
compile(b2.decode('utf-8-sig'), out, 'exec')
print('compile OK', flush=True)


def committed(pyc):
    ok = pyc[:-4] + 'OK.py'
    return open(ok, 'rb').read().replace(b'\r\n', b'\n') if os.path.exists(ok) else None


assert h16(ANA) == '996a1b1acf143458' and h16(GEN) == '566ff5c502276e48'
try:
    shutil.copyfile(R79, ANA)
    shutil.copyfile(out, GEN)
    for k, p in sorted(PYCS.items()):
        r = subprocess.run([sys.executable, '-X', 'utf8', M + '/pycdc.py', p],
                           capture_output=True, cwd=M, timeout=140)
        q = r.stdout.replace(b'\r\n', b'\n')
        c = committed(p)
        st = 'IDENTICAL' if c is not None and q == c else ('CHANGED' if c is not None else 'NOBASE')
        if len(r.stdout) < 2000:
            st = 'STUB/' + st
        print('   %-12s rc=%d bytes=%d %s' % (k, r.returncode, len(r.stdout), st), flush=True)
        if k == 'realtime' and len(r.stdout) > 2000:
            o = M + '/out/rt_stack_%s.py' % h16(out)
            open(o, 'wb').write(r.stdout)
            j = subprocess.run([sys.executable, '-X', 'utf8', SPR + '/rounds/round41/oracle_diff_r104.py', o],
                               capture_output=True, timeout=150)
            for l in j.stdout.decode('utf-8', 'replace').splitlines():
                if 'ours=' in l or 'DELTAS' in l or 'indeg' in l or 'units=' in l or 'Failure' in l:
                    print('     ', l.strip(), flush=True)
            a = subprocess.run([sys.executable, '-X', 'utf8', SPR + '/rounds/round41/hunk_attribution_r107.py', o],
                               capture_output=True, timeout=60)
            for l in a.stdout.decode('utf-8', 'replace').splitlines()[:3]:
                print('     ', l.strip(), flush=True)
finally:
    shutil.copyfile(PG, GEN)
    shutil.copyfile(PA, ANA)
    print('restored ana=%s gen=%s' % (h16(ANA) == '996a1b1acf143458', h16(GEN) == '566ff5c502276e48'), flush=True)
print('STACK=' + out)
