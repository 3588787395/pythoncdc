import os
import subprocess
import sys

ROOT = 'D:/Temp/r95'
REPO = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main'
SP = REPO + '/site-packages/'
FILES = [
    'IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc',
    'IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc',
    'IQCommon/util/replace_utils.pyc',
    'IQEngine/plugins/plugin_system_risk_calculation/function.pyc',
    'fly/data/quote.pyc',
    'fly/data/quotation.pyc',
    'IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc',
    'IQCommon/arg_checker.pyc',
    'IQData/utils/arg_checker.pyc',
    'IQEngine/utils/arg_checker.pyc',
    'IQCommon/profiler_func.pyc',
    'IQData/utils/profiler_func.pyc',
    'IQEngine/utils/profiler_func.pyc',
]

env = dict(os.environ, PYTHONIOENCODING='utf-8')
for i, rel in enumerate(FILES):
    pyc = SP + rel
    if not os.path.isfile(pyc):
        print('MISSING %s' % pyc)
        continue
    out = '%s/out/panel_%02d.py' % (ROOT, i)
    if os.path.exists(out):
        os.remove(out)
    r = subprocess.run([sys.executable, '-X', 'utf8', 'pycdc.py', pyc, '-o', out],
                       cwd=ROOT, capture_output=True, text=True, encoding='utf-8',
                       errors='replace', timeout=240)
    size = os.path.getsize(out) if os.path.exists(out) else -1
    if size in (-1, 0, 99):
        print('%s: PRODUCER FAILED rc=%d %s' % (rel, r.returncode, (r.stderr or '')[-200:]))
        continue
    j = subprocess.run([sys.executable, '-X', 'utf8', 'scripts/pyc_verify.py', 'single', pyc,
                        '--source', out],
                       cwd=ROOT, capture_output=True, text=True, encoding='utf-8',
                       errors='replace', timeout=240)
    txt = (j.stdout or '') + (j.stderr or '')
    verdict = [l for l in txt.splitlines() if 'units=' in l]
    bad = [l for l in txt.splitlines() if l.strip().startswith('***')]
    print('%s -> %s' % (rel, verdict[-1].strip() if verdict else 'NO VERDICT'))
    for b in bad[:3]:
        print('    resid: %s' % b.strip()[:120])
