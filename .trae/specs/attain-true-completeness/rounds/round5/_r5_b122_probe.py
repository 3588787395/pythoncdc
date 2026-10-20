# -*- coding: utf-8 -*-
"""R5 B122 hang 定位：计数包装 _identify_nested_match_regions + 周期采样栈。

用法: python -X utf8 _r5_b122_probe.py <pyc> <out_ok.py> <trace_txt> <count_txt> [sample_sec=5] [max_calls=60]
"""
import faulthandler
import os
import runpy
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
pyc, ok, trace_path, cnt_path = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
sample_sec = float(sys.argv[5]) if len(sys.argv) > 5 else 5.0
max_calls = int(sys.argv[6]) if len(sys.argv) > 6 else 60

trace = open(trace_path, 'w', encoding='utf-8')
cnt = open(cnt_path, 'w', encoding='utf-8')
state = {'calls': 0, 'lines': 0}


def log(msg):
    if state['lines'] < 400:
        cnt.write(msg + '\n')
        cnt.flush()
        state['lines'] += 1


def sampler():
    i = 0
    while True:
        time.sleep(sample_sec)
        i += 1
        trace.write('=== sample %d at %ds ===\n' % (i, int(i * sample_sec)))
        faulthandler.dump_traceback(file=trace, all_threads=False)
        trace.flush()


threading.Thread(target=sampler, daemon=True).start()

sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg import region_analyzer as RA  # noqa: E402

orig_id = RA.RegionAnalyzer._identify_nested_match_regions
orig_collect = RA.RegionAnalyzer._collect_nested_match_region


def wrap_id(self, parent_regions, existing_match_regions):
    state['calls'] += 1
    c = state['calls']
    log('id-call=%d parents=%d existing=%d types=%s' % (
        c, len(parent_regions or []), len(existing_match_regions or []),
        ','.join(type(p).__name__ for p in (parent_regions or [])[:6])))
    if c > max_calls:
        raise RuntimeError('ABORT after %d calls' % max_calls)
    r = orig_id(self, parent_regions, existing_match_regions)
    log('  id-call=%d ret=%d' % (c, len(r)))
    return r


def wrap_collect(self, candidate_block, parent_blocks, exclude_blocks):
    state.setdefault('collect', 0)
    state['collect'] += 1
    if state['collect'] <= 200:
        log('collect#%d cand=%s parent_n=%d excl_n=%d' % (
            state['collect'], getattr(candidate_block, 'start_offset', '?'),
            len(parent_blocks or []), len(exclude_blocks or [])))
    r = orig_collect(self, candidate_block, parent_blocks, exclude_blocks)
    if state['collect'] <= 200:
        log('  collect#%d ret=%s blocks=%d' % (
            state['collect'], 'None' if r is None else 'REG',
            len(r.blocks) if r else 0))
    return r


RA.RegionAnalyzer._identify_nested_match_regions = wrap_id
RA.RegionAnalyzer._collect_nested_match_region = wrap_collect

sys.argv = ['pycdc.py', pyc, '-o', ok]
try:
    runpy.run_path(os.path.join(ROOT, 'pycdc.py'), run_name='__main__')
except SystemExit as e:
    log('SystemExit %s' % e)
except Exception as e:
    log('EXC %r' % e)
finally:
    log('id-calls total=%d collect=%d' % (state['calls'], state.get('collect', 0)))
    trace.close()
    cnt.close()
