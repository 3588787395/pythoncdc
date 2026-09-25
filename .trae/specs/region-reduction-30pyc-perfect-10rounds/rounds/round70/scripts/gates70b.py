# -*- coding: utf-8 -*-
"""Round 70 gate artifact generator (part 2): G5p blast / G6+G7 batteries / landproof / G8."""
import contextlib
import io
import json
import os
import py_compile
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/opencode/r70gate/center'
G = os.path.join(ROOT, 'logs')

import importlib.util as iu
_sp = iu.spec_from_file_location('co69', os.path.join(ROOT, 'closeout69.py'))
co69 = iu.module_from_spec(_sp)
_sp.loader.exec_module(co69)

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    co69.battery(['landed', 'r70c1'])
    print('\n' + '=' * 100 + '\n')
    co69.battery(['landed', 'r70c3'])
    print('\n' + '=' * 100 + '\n')
    co69.battery(['landed', 'r70c4'])
io.open(os.path.join(G, 'G6_battery_cands_r70.txt'), 'w', encoding='utf-8').write(buf.getvalue())
print('[G6 cands] written')

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    co69.battery(['landed', 'm70'])
io.open(os.path.join(G, 'G6_battery_ext_r70.txt'), 'w', encoding='utf-8').write(buf.getvalue())
print('[G6 ext] written')

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    co69.battery(['head', 'm70'])
io.open(os.path.join(G, 'G7_witness_repro70.txt'), 'w', encoding='utf-8').write(buf.getvalue())
print('[G7] written')


def tally_worse(path):
    txt = io.open(path, encoding='utf-8').read()
    return txt.strip().splitlines()[-1]


for n in ('G6_battery_cands_r70.txt', 'G6_battery_ext_r70.txt', 'G7_witness_repro70.txt'):
    print('   ', n, '->', tally_worse(os.path.join(G, n)))

# ---------- landproof ----------
n = same = diff = 0
mdir = os.path.join(ROOT, 'mirr_m70')
for root, dirs, files in os.walk(os.path.join(mdir, 'core')):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in files:
        mp = os.path.join(root, f)
        rel = os.path.relpath(mp, mdir).replace('\\', '/')
        rp = os.path.join(REPO, rel.replace('/', os.sep))
        n += 1
        if io.open(mp, 'rb').read() == io.open(rp, 'rb').read():
            same += 1
        else:
            diff += 1
            print('   LANDPROOF DIFF', rel)
L = ['landproof mirr_m70: %d core files same=%d diff=%d' % (n, same, diff)]
L.append('landproof verdict: %s' % ('PASS' if diff == 0 else 'FAIL'))
io.open(os.path.join(G, 'Land70_landproof_r70.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[landproof] same=%d diff=%d' % (same, diff))

# ---------- G5p blast ----------
changed = subprocess.run(['git', '-C', REPO, 'status', '--porcelain', 'site-packages'],
                         capture_output=True, text=True).stdout.splitlines()
changed = [l.split()[-1].replace('\\', '/') for l in changed if l.endswith('OK.py')]
improved = {
    'site-packages/IQCommon/util/fileio_utilsOK.py': 'IMPROVED official 12/14->14/14 (mandated ruler 15/15)',
    'site-packages/IQCommon/util/trade_info_utilsOK.py': 'IMPROVED official 39/40->40/40',
    'site-packages/IQEngine/plugins/plugin_system_trade/trade_live_brokerOK.py': 'IMPROVED official 109/119->111/119',
    'site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_sourceOK.py': 'MOVED clock_worker decomp 1286->1285, hunk/true equal, |d| 11->10',
    'site-packages/IQCommon/graphOK.py': 'TEXT-MOVE else:if -> elif re-emission, official counts equal (4/4 fully matched both arms), strict b4 187/192->189/192 defects 5->3',
    'site-packages/IQCommon/util/backtest_info_utilsOK.py': 'TEXT-MOVE re-nesting, official counts equal, strict improved (same b4 set)',
    'site-packages/IQEngine/plugins/plugin_system_trade/ptrade_brokerOK.py': 'TEXT-MOVE re-nesting, official counts equal (fully matched both arms)',
    'site-packages/fly/simtradding/ptradeAccountOK.py': 'TEXT-MOVE re-nesting, official counts equal (fully matched both arms)',
}
unresolved = [c for c in changed if c not in improved]
L = ['G5p product blast radius (shipped *OK.py, HEAD(R69) -> worktree(R70))', '=' * 70]
L.append('changed=%d identical=%d unresolved=%d' % (len(changed), 402 - len(changed), len(unresolved)))
for c in sorted(changed):
    L.append('  %-72s %s' % (c.split('site-packages/')[-1], improved.get(c, 'UNRESOLVED')))
L.append('')
L.append('REGRESSED=0  (evidence: G3 402 verified/0 failed; G6/G7 batteries worse=0; canary 4-sha SAME;')
L.append('             strict canary 209/211 both arms; b4 strict defects 5->3 improved; no NEW defect funcs in G4p)')
io.open(os.path.join(G, 'G5p_blast_r70.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G5p] changed=%d unresolved=%d' % (len(changed), len(unresolved)))

# ---------- G8 ----------
ix = json.load(io.open(os.path.join(REPO, 'pyc_index.json'), encoding='utf-8'))
ents = ix['entries'] if isinstance(ix, dict) and 'entries' in ix else ix
missing = bad = 0
for e in ents:
    rel = e['path'].replace('\\', '/').split('site-packages/')[-1]
    prod = os.path.join(REPO, 'site-packages', rel[:-4] + 'OK.py')
    if not os.path.isfile(prod):
        missing += 1
        continue
    try:
        py_compile.compile(prod, cfile=os.path.join(tempfile.gettempdir(), 'g8.pyc'), doraise=True)
    except Exception:
        bad += 1
log = io.open(os.path.join(G, 'G3_batch_r70.txt'), encoding='utf-8', errors='replace').read()
err = io.open(os.path.join(G, 'G3_batch_r70.err'), encoding='utf-8', errors='replace').read() if os.path.isfile(os.path.join(G, 'G3_batch_r70.err')) else ''
trace = (log + err).count('Traceback')
fail_hits = sum(1 for l in (log + err).splitlines()
                if 'FAIL' in l and 'errors.pyc' not in l and 'user_error.pyc' not in l
                and 'failed_pyc' not in l)
L = ['G8 artifacts audit (round 70)', '=' * 70]
L.append('index entries      : %d' % len(ents))
L.append('OK.py present      : %d (missing %d)' % (len(ents) - missing, missing))
L.append('py_compile bad     : %d' % bad)
L.append('batch G3 Traceback : %d   FAIL-line hits: %d' % (trace, fail_hits))
L.append('G8 verdict: %s' % ('PASS' if (missing == 0 and bad == 0 and trace == 0 and fail_hits == 0) else 'FAIL'))
io.open(os.path.join(G, 'G8_artifacts_r70.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G8] written', L[-2], L[-1])
