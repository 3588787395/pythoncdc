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
want = {'realtime_event_source.pyc': 'realtime', 'quote.pyc': 'quote', 'real_quote.pyc': 'real_quote',
        'trade_live_broker.pyc': 'broker', 'function.pyc': 'function', 'replace_utils.pyc': 'replace_utils',
        'quotation.pyc': 'quotation', 'order_api.pyc': 'order_api', 'klinedata.pyc': 'klinedata',
        'handlers.pyc': 'handlers'}
PYCS = {}
for p in paths:
    b = os.path.basename(p)
    if b in want:
        PYCS.setdefault(want[b], p)

lines = open(R81, 'rb').read().decode('utf-8-sig').split('\r\n')
targets = []
for i, l in enumerate(lines):
    s = l.strip()
    if s == 'self.generated_blocks.add(b)':
        for back in range(1, 5):
            if lines[i - back].strip().startswith('for b in region.else_blocks:'):
                targets.append(('else_blocks-claim', i))
                break
    if s == 'self.generated_blocks.add(_nb)':
        for back in range(1, 7):
            if lines[i - back].strip() == 'for _nb in _nr.blocks:':
                targets.append(('nr_blocks-claim', i))
                break
print('targets:', [(t, i + 1) for t, i in targets], flush=True)
dn = next(i for i, l in enumerate(lines) if l.strip().startswith('def _if_generate_normal('))
targets = [t for t in targets if t[0] == 'nr_blocks-claim' or t[1] > dn]
print('_if_generate_normal def at %d; kept targets: %s' % (dn + 1, [(t, i + 1) for t, i in targets]), flush=True)
assert len(targets) >= 2, 'expected the claim statements, got %d' % len(targets)
for t, i in targets:
    lines[i] = ' ' * (len(lines[i]) - len(lines[i].lstrip())) + 'pass'
body = ('\ufeff' + '\r\n'.join(lines)).lstrip('\ufeff').encode('utf-8')
p = 'D:/Temp/merge_r108/gen_r2190E_ledger_plus_pair.py'
open(p, 'wb').write(body)
b = open(p, 'rb').read()
compile(b.decode('utf-8-sig'), p, 'exec')
print('E sha16=%s size=%d bareLF=%d CRCRCR=%d compile OK' % (
    h16(p), len(b), sum(1 for i, c in enumerate(b) if c == 10 and (i == 0 or b[i - 1] != 13)),
    b.count(b'\r\r\n')), flush=True)


def committed(pyc):
    ok = pyc[:-4] + 'OK.py'
    return open(ok, 'rb').read().replace(b'\r\n', b'\n') if os.path.exists(ok) else None


def measure(variant, label, ana):
    print('=== measure %s ana=%s gen=%s ===' % (label, h16(ana)[:8], h16(variant)[:8]), flush=True)
    try:
        shutil.copyfile(ana, ANA)
        shutil.copyfile(variant, GEN)
        bad = []
        for k, pp in sorted(PYCS.items()):
            if k not in ('realtime', 'broker', 'klinedata', 'quote', 'real_quote', 'function', 'replace_utils'):
                continue
            r = subprocess.run([sys.executable, '-X', 'utf8', M + '/pycdc.py', pp],
                               capture_output=True, cwd=M, timeout=110)
            q = r.stdout.replace(b'\r\n', b'\n')
            c = committed(pp)
            same = c is not None and q == c
            if k != 'realtime' and not same:
                bad.append(k)
            if k == 'realtime':
                o = M + '/out/rt_%s.py' % label
                open(o, 'wb').write(r.stdout)
                j = subprocess.run([sys.executable, '-X', 'utf8', SPR + '/rounds/round41/oracle_diff_r104.py', o],
                                   capture_output=True, timeout=120)
                for l in j.stdout.decode('utf-8', 'replace').splitlines():
                    if 'ours=' in l or 'DELTAS' in l or 'indeg' in l or 'units=' in l:
                        print('   ', l.strip(), flush=True)
        print('   collateral_changed=%s' % bad, flush=True)
    finally:
        shutil.copyfile(PG, GEN)
        shutil.copyfile(PA, ANA)
        print('   restored ana=%s gen=%s' % (h16(ANA) == '996a1b1acf143458', h16(GEN) == '566ff5c502276e48'), flush=True)


measure(p, 'r2190E_with79', R79)
