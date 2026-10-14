import ast
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


def h16(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()[:16]


paths = [os.path.join(ROOT, l.strip()) for l in open(CL, encoding='utf-8') if l.strip()]
want = {'realtime_event_source.pyc': 'realtime', 'quote.pyc': 'quote',
        'real_quote.pyc': 'real_quote', 'trade_live_broker.pyc': 'broker',
        'function.pyc': 'function', 'replace_utils.pyc': 'replace_utils'}
PYCS = {}
for p in paths:
    b = os.path.basename(p)
    if b in want:
        PYCS.setdefault(want[b], p)

base_gen = open(LAND, 'rb').read()
if h16(GEN) != '566ff5c502276e48':
    shutil.copyfile(LAND, GEN)
src = base_gen.decode('utf-8-sig')
lines = src.split('\r\n')
tree = ast.parse(src)
tgt = None
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == '_if_generate_normal':
        tgt = node
print('method _if_generate_normal lines %d..%d' % (tgt.lineno, tgt.end_lineno))
# find the two claim loops INSIDE the method that add to generated_blocks from then_blocks/else_blocks
loops = []
for node in ast.walk(tgt):
    if isinstance(node, ast.For) and isinstance(node.iter, ast.Attribute) and node.iter.attr in ('then_blocks', 'else_blocks'):
        blk = ast.dump(node)
        if 'generated_blocks' in blk:
            loops.append((node.lineno, node.end_lineno, node.iter.attr))
print('claim loops found:', loops)
neut = set()
for a, b, which in loops:
    for i in range(a - 1, b):
        if lines[i].strip() == 'self.generated_blocks.add(b)':
            neut.add(i)
print('claim statements neutered:', sorted(i + 1 for i in neut))
keep = [(' ' * (len(lines[i]) - len(lines[i].lstrip())) + 'pass') if i in neut else lines[i]
        for i in range(len(lines))]
drop = set()
print('lines removed:', len(lines) - len(keep))
new = ('\ufeff' + '\r\n'.join(keep).lstrip('\ufeff')).encode('utf-8')
out = 'D:/Temp/merge_r108/gen_r2183_nooverclaim.py'
open(out, 'wb').write(new)
b2 = open(out, 'rb').read()
print('variant sha16=%s size=%d bareLF=%d CRCRCR=%d' % (
    h16(out), len(b2), sum(1 for i, c in enumerate(b2) if c == 10 and (i == 0 or b2[i - 1] != 13)),
    b2.count(b'\r\r\n')))
try:
    compile(b2.decode('utf-8-sig'), out, 'exec')
    print('compile OK')
except SyntaxError as e:
    print('SYNTAX', e)
    sys.exit(1)


def committed(pyc):
    ok = pyc[:-4] + 'OK.py'
    return open(ok, 'rb').read().replace(b'\r\n', b'\n') if os.path.exists(ok) else None


assert h16(ANA) == '996a1b1acf143458'
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
            o = M + '/out/rt_nooverclaim_%s.py' % h16(out)
            open(o, 'wb').write(r.stdout)
            j = subprocess.run([sys.executable, '-X', 'utf8', SPR + '/rounds/round41/oracle_diff_r104.py', o],
                               capture_output=True, timeout=150)
            for l in j.stdout.decode('utf-8', 'replace').splitlines():
                if 'hunks_vs_ORACLE' in l or 'DELTAS' in l or 'indeg' in l or 'units=' in l:
                    print('     ', l.strip(), flush=True)
finally:
    shutil.copyfile(PG, GEN)
    shutil.copyfile(PA, ANA)
    print('restored ana=%s gen=%s' % (h16(ANA) == '996a1b1acf143458', h16(GEN) == '566ff5c502276e48'))
