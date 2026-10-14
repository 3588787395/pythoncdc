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
assert lines[22497].strip() == 'for b in region.then_blocks:'
assert lines[26907].strip() == 'for _nb in _nr.blocks:'
assert lines[26910].strip() == 'self.generated_blocks.add(_nb)'
assert lines[26911].strip() == 'self.generated_offsets.add(_nb.start_offset)'

PRE_A = [
    '                # [R21-88] render-scoped claim: only blocks this branch rendered.',
    '                _r2188_rendered = set()',
    '                _r2188_rendered.update(getattr(region, "elif_conditions", None) or [])',
    '                for _r2188_body in (getattr(region, "elif_bodies", None) or []):',
    '                    _r2188_rendered.update(_r2188_body)',
    '                _r2188_rendered.update(getattr(region, "elif_final_else", None) or [])',
    '                _r2188_rendered.update(getattr(region, "chained_compare_blocks", None) or [])',
    '                _r2188_rendered.add(_r23_or_then)',
    '                _r2188_rendered.add(_r23_or_else)',
    '                _r2188_rendered.add(_r23_or_rhs)',
]
PRE_B = [
    '                # [R21-88] render-scoped claim for the dispatched nested region: its own arm',
    '                # lists, not every block that happens to share its membership set.',
    '                _r2188_nr_rendered = set()',
    '                for _r2188_k, _r2188_v in vars(_nr).items():',
    '                    if _r2188_k.endswith("_blocks") or _r2188_k in ("elif_conditions", "elif_final_else", "condition_block", "header_block", "entry", "merge_block", "back_edge_block"):',
    '                        if isinstance(_r2188_v, (list, tuple, set, frozenset)):',
    '                            _r2188_nr_rendered.update(_r2188_v)',
    '                        elif _r2188_v is not None:',
    '                            _r2188_nr_rendered.add(_r2188_v)',
    '                for _r2188_l in (getattr(_nr, "elif_bodies", None) or []):',
    '                    _r2188_nr_rendered.update(_r2188_l)',
]


def build(tag):
    out = list(lines)
    out[22499] = '                        if b not in self.generated_blocks and b in _r2188_rendered:'
    out[22503] = '                        if b not in self.generated_blocks and b in _r2188_rendered:'
    out[26910] = '                    if _nb in _r2188_nr_rendered:'
    out[26911] = '                        self.generated_blocks.add(_nb)'
    out.insert(26912, '                        self.generated_offsets.add(_nb.start_offset)')
    out[26907:26907] = PRE_B
    out[22497:22497] = PRE_A
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


v = build('r2188C_both_renderscoped')
measure(v, R79, 'r2188C_with79')
