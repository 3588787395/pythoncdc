# -*- coding: utf-8 -*-
"""Detached runner: mandated 尺单支复测 real_quoteOK.py。

结果落 dump/pycverify_rq.json + dump/pycverify_rq_log.txt（边跑边 flush，
避免缓冲导致长任务读不到输出）。任何 BaseException（含 segfault 之外的）
都先落盘。
"""
import io
import json
import os
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
PYLINGUAL = r'D:\Desktop\ptrade相关\pylingual'
PYC = r'F:/Downloads/pythoncdc-main/site-packages/IQData/plugins/plugin_system_realquote/real_quote.pyc'
CAND = r'F:/Downloads/pythoncdc-main/site-packages/IQData/plugins/plugin_system_realquote/real_quoteOK.py'
OUT = os.path.join(HERE, 'dump', 'pycverify_rq.json')
LOG = os.path.join(HERE, 'dump', 'pycverify_rq_log.txt')
sys.stdout.reconfigure(encoding='utf-8')

logf = io.open(LOG, 'w', encoding='utf-8')


def log(*a):
    s = ' '.join(str(x) for x in a)
    logf.write(s + '\n')
    logf.flush()
    print(s, flush=True)


def dump(obj, path):
    io.open(path, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(obj, ensure_ascii=False, indent=1))


def main():
    t0 = time.time()
    log('start', time.strftime('%H:%M:%S'), 'pylingual root=', PYLINGUAL)
    vp = r'F:/Downloads/pythoncdc-main/scripts/pyc_verify.py'
    import importlib.util
    spec = importlib.util.spec_from_file_location('pyc_verify_r75', vp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    log('loaded pyc_verify from', vp)
    cp = mod.load_compare_pyc(PYLINGUAL)
    log('compare_pyc loaded from', getattr(cp, '__module__', '?'))
    import tempfile, shutil
    tmp = tempfile.mkdtemp(prefix='pycverify_rq_')
    try:
        t1 = time.time()
        log('evaluate begin')
        row = mod.evaluate(PYC, CAND, tmp, cp)
        log('evaluate end %.1fs status=%s units=%s/%s' % (
            time.time() - t1, row.get('status'),
            row.get('units_success'), row.get('units_total')))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    row['elapsed_s'] = round(time.time() - t0, 1)
    row['ts'] = time.strftime('%Y-%m-%d %H:%M:%S')
    dump(row, OUT)
    log('wrote', OUT, 'status=', row.get('status'))


if __name__ == '__main__':
    try:
        main()
    except BaseException as e:
        log('FAIL', repr(e))
        log(traceback.format_exc())
        dump({'ok': False, 'error': repr(e), 'trace': traceback.format_exc(),
              'ts': time.strftime('%Y-%m-%d %H:%M:%S')}, OUT)
