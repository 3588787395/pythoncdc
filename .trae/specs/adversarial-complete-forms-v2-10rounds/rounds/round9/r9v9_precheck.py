import json
import os
import re
import shutil
import subprocess
import sys

MAIN = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
WT = r'D:\Temp\opencode\wt_r8pre'

PROBES = {
    'r3_e05': 'test_repros/round3/e05_g3_compare_chain.pyc',
    'r3_e10': 'test_repros/round3/e10_g7_call_args.pyc',
    'r4_b109_loopelse': 'test_repros/round4/r4v4r_b109_loopelse.pyc',
    'r5_13_for_else_cross': 'test_repros/round5/r5v5_13_for_else_cross.pyc',
    'r8_b104_chain5': 'test_repros/round8/r8v8rev3_b104_chain5_battery.pyc',
    'r8_b104_opdeep': 'test_repros/round8/r8v8rev3_b104_opdeep_battery.pyc',
    'r8_b104_exprtail': 'test_repros/round8/r8v8rev3_b104_exprtail_battery.pyc',
    'n9_b104_whilehost': 'test_repros/round9/n9v9_b104_whilehost.pyc',
    'n9_stmt_sweep': 'test_repros/round9/n9v9_stmt_sweep.pyc',
}

STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')
FAIL_RE = re.compile(r'^\s*\*\*\*.*?:\s*Failure.*$')


def run(cmd, timeout=200):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=WT,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return -9, 'TIMEOUT'


def main():
    rows = []
    for name, rel in PROBES.items():
        src = os.path.join(MAIN, rel.replace('/', os.sep))
        dst = os.path.join(WT, rel.replace('/', os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        for s in (src, src[:-4] + '.py'):
            if os.path.exists(s):
                shutil.copy2(s, dst if s.endswith('.pyc') else dst[:-4] + '.py')
        rc_regen, _ = run([sys.executable, os.path.join(WT, 'pycdc.py'), dst, '-o', dst[:-4] + 'OK.py'])
        rc, out = run([sys.executable, os.path.join(WT, 'scripts', 'pyc_verify.py'), 'single', dst])
        status, us, ut = None, None, None
        for line in out.splitlines():
            m = STAT_RE.search(line)
            if m:
                status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
        fails = [l.strip() for l in out.splitlines() if FAIL_RE.match(l)]
        rows.append({'name': name, 'pyc': rel, 'regen_rc': rc_regen, 'status': status,
                     'units_success': us, 'units_total': ut, 'failures': fails})
        print('[%-22s] regen_rc=%s %-8s %s/%s' % (name, rc_regen, status, us, ut), flush=True)
        for f in fails:
            print('    ' + f)
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, 'r9v9_premerge_check.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print('-> saved r9v9_premerge_check.json (worktree 91f8d27d = pre-merge round8 terminal)')


if __name__ == '__main__':
    main()
