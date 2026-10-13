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
F5 = os.path.join(SPR, 'rounds/round41/CANDIDATE_r2177f5_996a1b1acf143458.py')
CL = os.path.join(SPR, 'rounds/round40/r95/corpus402.txt')
LAND = os.path.join(ROOT, 'core/cfg/region_ast_generator.py')


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

lines = open(LAND, 'rb').read().decode('utf-8-sig').split('\r\n')
assert lines[22497].strip() == 'for b in region.then_blocks:', lines[22497][:80]
assert lines[22499].strip().startswith('if b not in self.generated_blocks and b not in'), lines[22499][:90]
assert lines[22501].strip() == 'for b in region.else_blocks:', lines[22501][:80]
assert lines[22503].strip() == 'if b not in self.generated_blocks:', lines[22503][:80]
assert lines[26910].strip() == 'self.generated_blocks.add(_nb)', lines[26910][:80]

PRE = [
    '                # [R21-87] render-scoped claim: a branch may mark consumed only the blocks',
    '                # it actually rendered. The or-chain graft renders the then operand plus the',
    '                # grafted elif arm lists, so every other member of then_blocks / else_blocks',
    '                # stays for the owning parent sequence.',
    '                _r2187_rendered = set()',
    '                _r2187_rendered.update(getattr(region, "elif_conditions", None) or [])',
    '                for _r2187_body in (getattr(region, "elif_bodies", None) or []):',
    '                    _r2187_rendered.update(_r2187_body)',
    '                _r2187_rendered.update(getattr(region, "elif_final_else", None) or [])',
    '                _r2187_rendered.update(getattr(region, "chained_compare_blocks", None) or [])',
    '                _r2187_rendered.add(_r23_or_then)',
    '                _r2187_rendered.add(_r23_or_else)',
    '                _r2187_rendered.add(_r23_or_rhs)',
]


def build(tag, neuter26911=False):
    out = list(lines)
    # statement replacements (indices are pre-insert; do them first)
    out[22499] = out[22499].replace(
        'if b not in self.generated_blocks and b not in (region.chained_compare_blocks or []):',
        'if b not in self.generated_blocks and b in _r2187_rendered:')
    out[22503] = '                        if b not in self.generated_blocks and b in _r2187_rendered:'
    if neuter26911:
        out[26910] = ' ' * (len(out[26910]) - len(out[26910].lstrip())) + 'pass'
    out[22497:22497] = PRE
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


def measure(variant, ana, label):
    print('=== measure %s ana=%s gen=%s ===' % (label, h16(ana)[:8], h16(variant)[:8]), flush=True)
    try:
        shutil.copyfile(ana, ANA)
        shutil.copyfile(variant, GEN)
        bad = []
        for k, p in sorted(PYCS.items()):
            r = subprocess.run([sys.executable, '-X', 'utf8', M + '/pycdc.py', p],
                               capture_output=True, cwd=M, timeout=100)
            q = r.stdout.replace(b'\r\n', b'\n')
            c = committed(p)
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


v_a = build('r2187A_renderscoped')
measure(v_a, R79, 'r2187A_with79')
if '--b' in sys.argv:
    v_b = build('r2187B_renderscoped_no26911', neuter26911=True)
    measure(v_b, R79, 'r2187B_with79')
if '--f5' in sys.argv:
    measure(v_a, F5, 'r2187A_withF5')
